"""PreToolUse hook (Bash) for Software Factory sessions.

Asks before irreversible, external or locally destructive commands (contract
rules 9.7 and 9.12) and denies shell file writes by factory subagents (rule
9.12). It never answers "allow", so the user's own permission rules still
decide everything it does not flag. When unsure, it asks.
"""

import codecs
import json
import os
from pathlib import Path
import re
import sys

from factory_scope import factory_roots

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}
MAX_DEPTH = 6
EXTERNAL = "irreversible or external (contract rule 9.7)"
LOCAL = "a local destructive action (contract rule 9.12)"
UNPARSED = "a command the gate could not fully parse, so it asks (contract rule 9.7)"
PIPED_SHELL = "a shell running commands from a pipe the gate cannot read (contract rule 9.7)"

OP_CHARS = set(";&|()<>")
OP_RE = re.compile(r";;|&&|\|\||\|&|<<<|<<-|<<|>>|&>>|&>|>&|<&|>\||<>|[;&|()<>]")
WRITE_OPS = {">", ">>", ">|", "&>", "&>>", "<>"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}
PYTHON = re.compile(r"python(\d+(\.\d+)*)?")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=")
PY_MODE = r"(?:mode\s*=\s*)?['\"](?:[wax][bt+]{0,2}|r\+b?|rb\+)['\"]"
PY_WRITE = re.compile(  # open(path, "w"), Path.open("w"), write_text(, write_bytes(
    r"write_text\(|write_bytes\(|\bopen\((?:[^()]|\([^()]*\))*?,\s*" + PY_MODE + r"|\.open\(\s*" + PY_MODE, re.S
)
GRAPHQL_DESTRUCTIVE = re.compile(r"mutation[\s\S]*\b(delete|remove|merge|close|archive|transfer)", re.I)
FALLBACK = re.compile(
    r"\bgit\b[^\n;&|]*\b(push|reset|clean|branch|checkout|restore|stash)\b"
    r"|\bgh\s+(pr|release|repo|secret|variable|workflow|issue|api)\b"
    r"|\brm\s+-"
    r"|\b(terraform|tofu|pulumi|kubectl|helm|vercel|netlify|flyctl|fly|wrangler|firebase|gcloud|aws|supabase|twine)\s"
    r"|\bcf\s+deploy\b"
    r"|\b(npm|pnpm|yarn|cargo)\b[^\n;&|]*\bpublish\b"
    r"|\bdocker\b[^\n;&|]*\bpush\b"
    r"|\b(sed|perl)\s[^\n;&|]*\s-\w*i"
    r"|\b(bash|sh|zsh|eval)\s"
    r"|\bpython[\d.]*\s[\s\S]*(write_text|write_bytes|open\()"
)

RISKY = re.compile(r"\b(push|reset|clean|delete|deploy|apply|destroy|publish|merge|rm)\b")

# Wrappers that run the rest of the line as a command, with the options that take a separate value.
WRAPPERS = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-U", "-r", "-t", "-D", "-T", "--user", "--group", "--host",
             "--prompt", "--chdir", "--role", "--type", "--other-user", "--close-from", "--command-timeout"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "command": set(), "builtin": set(), "exec": {"-a"}, "time": set(), "nohup": set(),
    "nice": {"-n", "--adjustment"}, "ionice": {"-c", "-n", "-p"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "stdbuf": {"-i", "-o", "-e"}, "caffeinate": {"-t", "-w"},
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a", "--max-args", "--max-procs", "--max-lines",
              "--delimiter", "--eof", "--max-chars", "--arg-file"},
    "npx": {"-p", "--package", "-c", "--call"}, "bunx": {"-p", "--package"},
    "coproc": set(), "!": set(), "{": set(), "if": set(), "then": set(), "elif": set(), "else": set(), "do": set(),
    "while": set(), "until": set(), "watch": {"-n", "--interval"},
}
CLI_ALIASES = {"netlify-cli": "netlify", "firebase-tools": "firebase", "flyctl": "fly"}
TWO_WORD_WRAPPERS = {("npm", "exec"), ("pnpm", "exec"), ("pnpm", "dlx"), ("yarn", "dlx"), ("yarn", "exec"),
                     ("uv", "run"), ("poetry", "run"), ("pipenv", "run"), ("bundle", "exec")}
TWO_WORD_ARGS = {"-p", "--package", "-c", "--call", "-w", "--workspace", "--with", "--from"}
STRING_OPTS = {"-S", "--split-string", "-c", "--call"}  # wrapper option values that are command strings

GH_ASK = {
    "pr": {"create", "merge", "ready", "close", "reopen"},
    "release": {"create", "delete", "edit", "upload"},
    "repo": {"create", "delete", "edit", "rename", "archive"},
    "secret": {"set", "delete", "remove"},
    "variable": {"set", "delete", "remove"},
    "workflow": {"run", "enable", "disable"},
    "issue": {"delete", "transfer"},
}
GH_API_ARGS = {"-X", "--method", "-H", "--header", "-f", "-F", "--field", "--raw-field", "--input", "-q", "--jq",
               "-t", "--template", "-p", "--preview", "--hostname", "--cache", "-R", "--repo"}
KUBE_ARGS = {"-n", "--namespace", "--context", "--kubeconfig", "--cluster", "--user", "-s", "--server", "--token"}
KUBE_WRITES = {"apply", "create", "delete", "patch", "replace", "scale", "edit", "rollout", "drain"}
HELM_ARGS = {"-n", "--namespace", "--kube-context", "--kubeconfig"}
WHOLE_TREE = {".", "./", ":/", "*"}
LEX_BUDGET = [5000]  # lex() calls allowed per hook run


def close_paren(text, i):
    """Index of the ")" that closes a "(" opened just before i, or -1. Ignores quotes (fails toward more scanning)."""
    depth = 1
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return -1


def raw_substitutions(text):
    """Command substitutions in an unquoted heredoc body, where quotes do not protect anything."""
    subs, i = [], 0
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            end = text.find("`", i + 1)
            if end < 0:
                raise ValueError("open backtick")
            subs.append(text[i + 1:end])
            i = end + 1
        elif text.startswith("$(", i):
            end = close_paren(text, i + 2)
            if end < 0:
                raise ValueError("open substitution")
            subs.append(text[i + 2:end])
            i = end + 1
        else:
            i += 1
    return subs


def lex(text):
    """Split shell text into tokens (text, is_operator), heredoc bodies (body, quoted) and command substitutions.

    Raises ValueError on an unclosed quote, substitution or heredoc, or when the lexing budget runs out.
    """
    LEX_BUDGET[0] -= 1
    if LEX_BUDGET[0] < 0:  # bounds the substitution retries below on hostile input
        raise ValueError("lexing budget exhausted")
    tokens, bodies, subs, pending = [], [], [], []
    word, started, quoted = [], False, False
    i, n = 0, len(text)

    def flush():
        nonlocal word, started, quoted
        if started:
            tokens.append(("".join(word), False))
            if len(tokens) > 1 and tokens[-2][1] and tokens[-2][0] in ("<<", "<<-"):
                pending.append(("".join(word), tokens[-2][0] == "<<-", quoted))
        word, started, quoted = [], False, False

    def substitution(j):
        if text[j] == "`":
            end = text.find("`", j + 1)
            if end < 0:
                raise ValueError("open backtick")
            subs.append(text[j + 1:end])
            return end + 1
        end = close_paren(text, j + 2)
        if end < 0:
            raise ValueError("open substitution")
        # A heredoc body inside $( ) may hold an unmatched ")" (a "1) item" list). When the naive
        # match does not lex, take the first later ")" whose inner text does.
        candidate = end
        for _ in range(50 if "<<" in text[j + 2:end] else 1):
            try:
                lex(text[j + 2:candidate])
                end = candidate
                break
            except ValueError:
                candidate = text.find(")", candidate + 1)
                if candidate < 0:
                    break
        subs.append(text[j + 2:end])
        return end + 1

    def read_bodies(j):
        for delim, tabs, is_quoted in pending:
            pos = j
            while True:
                if pos >= n:
                    raise ValueError("heredoc without its closing delimiter")
                end = text.find("\n", pos)
                end = n if end < 0 else end
                line = text[pos:end]
                if (line.lstrip("\t") if tabs else line) == delim:
                    body = text[j:pos]
                    bodies.append((body, is_quoted))
                    if not is_quoted:
                        subs.extend(raw_substitutions(body))
                    j = min(end + 1, n)
                    break
                pos = end + 1
        pending.clear()
        return j

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "\\":
            if nxt != "\n":  # backslash-newline is a line continuation
                word.append(nxt)
                started = quoted = True
            i += 2
        elif c == "'":
            end = text.find("'", i + 1)
            if end < 0:
                raise ValueError("open single quote")
            word.append(text[i + 1:end])
            started = quoted = True
            i = end + 1
        elif c == '"':
            started = quoted = True
            i += 1
            while True:
                if i >= n:
                    raise ValueError("open double quote")
                c = text[i]
                if c == '"':
                    i += 1
                    break
                if c == "\\" and i + 1 < n and text[i + 1] in '$`"\\\n':
                    if text[i + 1] != "\n":
                        word.append(text[i + 1])
                    i += 2
                elif c == "`" or text.startswith("$(", i):
                    end = substitution(i)
                    word.append(text[i:end])
                    i = end
                else:
                    word.append(c)
                    i += 1
        elif c == "$" and nxt == "'":  # ANSI-C quoting: bash decodes the escapes
            j = i + 2
            while j < n and text[j] != "'":
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ValueError("open single quote")
            word.append(codecs.decode(text[i + 2:j].encode("latin-1", "backslashreplace"), "unicode_escape"))
            started = quoted = True
            i = j + 1
        elif c == "$" and nxt == '"':  # locale quoting: same as a double-quoted string
            i += 1
        elif c == "`" or (c in "$<>" and nxt == "("):
            end = substitution(i)
            word.append(text[i:end])
            started = True
            i = end
        elif c == "\n":
            flush()
            tokens.append(("\n", True))
            i += 1
            if pending:
                i = read_bodies(i)
        elif c in " \t\r":
            flush()
            i += 1
        elif c == "#" and not started:
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif c in OP_CHARS:
            if started and not quoted and c in "<>" and "".join(word).isdigit():
                word, started = [], False  # "2>" names a file descriptor, not an argument
            flush()
            j = i
            while j < n and text[j] in OP_CHARS:
                j += 1
            run = text[i:j]
            if run.endswith("<<") and text[j:j + 1] == "-":
                run, j = run + "-", j + 1
            tokens.extend((op, True) for op in OP_RE.findall(run))
            i = j
        else:
            word.append(c)
            started = True
            i += 1
    flush()
    if pending:
        raise ValueError("heredoc without a body")
    return tokens, bodies, subs


def pipelines(tokens):
    """Group tokens into pipelines of simple commands. Redirect operators stay inside their command."""
    result, line, seg = [], [], []
    for tok, is_op in tokens:
        if is_op and "<" not in tok and ">" not in tok:
            line.append(seg)
            seg = []
            if tok not in ("|", "|&"):
                result.append(line)
                line = []
        else:
            seg.append((tok, is_op))
    line.append(seg)
    result.append(line)
    return [[s for s in p if s] for p in result]


def split_redirects(seg):
    """Return (words, write targets, uses heredoc or herestring)."""
    words, writes, heredoc, i = [], [], False, 0
    while i < len(seg):
        tok, is_op = seg[i]
        if not is_op:
            words.append(tok)
            i += 1
            continue
        has_target = i + 1 < len(seg) and not seg[i + 1][1]
        target = seg[i + 1][0] if has_target else ""
        if tok.startswith("<<"):
            heredoc = True
        elif tok in WRITE_OPS or (tok == ">&" and not (target.isdigit() or target == "-")):
            writes.append(target)
        i += 2 if has_target else 1
    return words, writes, heredoc


def positionals(args, with_arg=()):
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-") and a != "-":
            skip = a in with_arg
        else:
            out.append(a)
    return out


def short_flags(args):
    return {c for a in args if a.startswith("-") and not a.startswith("--") for c in a[1:]}


def tmp_roots():
    roots = set()
    for root in (os.environ.get("TMPDIR"), "/tmp", "/private/tmp"):
        if root:
            real = os.path.realpath(root)
            if real != os.sep:
                roots.add(real.rstrip(os.sep))
    return roots


def under_tmp(path, cwd):
    """True when path resolves strictly inside a temp directory (never the temp directory itself)."""
    path = os.path.expanduser(os.path.expandvars(path))
    if not path or any(ch in path for ch in "$`{}"):
        return False
    parts = path.split("/")
    if any(ch in part for part in parts[:-1] for ch in "*?["):
        return False  # a glob in a parent directory could match ".."
    real = os.path.realpath(os.path.join(cwd, path))
    return any(real.startswith(root + os.sep) for root in tmp_roots())


def safe_write_target(path, cwd):
    return path.startswith("/dev/") or under_tmp(path, cwd)


def git_rule(args):
    i, aliases = 0, {}
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-c" and i + 1 < len(args) and args[i + 1].startswith("alias."):
            key, _, value = args[i + 1].partition("=")
            aliases[key[6:]] = value
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    if sub in aliases:  # inline alias: judge the expansion
        if aliases[sub].startswith("!"):
            return UNPARSED
        expansion = aliases[sub].split()
        if expansion:
            sub, rest = expansion[0], expansion[1:] + rest
    flags = short_flags(rest)
    if sub == "push":
        return None if "--dry-run" in rest or "-n" in rest else EXTERNAL
    if sub == "reset" and "--hard" in rest:
        return LOCAL
    if sub == "clean" and ("--force" in rest or "f" in flags):
        return LOCAL
    if sub == "branch" and ("D" in flags or (("--delete" in rest or "d" in flags) and ("--force" in rest or "f" in flags))):
        return LOCAL
    if sub == "restore" and ("--staged" in rest or "S" in flags) and not ("--worktree" in rest or "W" in flags):
        return None  # only unstages
    if sub in ("checkout", "restore") and WHOLE_TREE & set(rest):
        return LOCAL
    if sub == "stash" and rest[:1] in (["drop"], ["clear"]):
        return LOCAL
    return None


def gh_rule(args):
    pos = positionals(args, {"-R", "--repo"})
    if pos[:1] == ["api"]:
        rest = args[args.index("api") + 1:]
        method, fields = "", False
        for j, a in enumerate(rest):
            if a in ("-X", "--method"):
                method = rest[j + 1] if j + 1 < len(rest) else ""
            elif a.startswith("--method="):
                method = a.split("=", 1)[1]
            elif a.startswith("-X"):
                method = a[2:]
            elif a in ("-f", "-F", "--field", "--raw-field", "--input") or a.startswith(
                    ("--field=", "--raw-field=", "--input=", "-f", "-F")):
                fields = True
        method = (method or ("POST" if fields else "GET")).upper()
        if method in ("DELETE", "PUT", "PATCH"):
            return EXTERNAL
        if method == "POST":
            endpoint = (positionals(rest, GH_API_ARGS) or [""])[0]
            if endpoint == "graphql":
                return EXTERNAL if GRAPHQL_DESTRUCTIVE.search(" ".join(rest)) else None
            return None if "/issues" in "/" + endpoint.lstrip("/") else EXTERNAL
        return None
    return EXTERNAL if len(pos) >= 2 and pos[1] in GH_ASK.get(pos[0], ()) else None


def rm_rule(args, cwd):
    recursive = force = done = False
    targets = []
    for a in args:
        if done or a == "-" or not a.startswith("-"):
            targets.append(a)
        elif a == "--":
            done = True
        elif a.startswith("--"):
            recursive |= len(a) > 2 and "--recursive".startswith(a)
            force |= len(a) > 2 and "--force".startswith(a)
        else:
            recursive |= "r" in a or "R" in a
            force |= "f" in a
    if recursive and force and not (targets and all(under_tmp(t, cwd) for t in targets)):
        return LOCAL
    return None


def rule(name, args, cwd):
    """Why this command needs the user's approval, or None."""
    pos = positionals(args)
    pairs = set(zip(pos, pos[1:]))
    if name == "git":
        return git_rule(args)
    if name == "gh":
        return gh_rule(args)
    if name == "rm":
        return rm_rule(args, cwd)
    if name in ("terraform", "tofu"):
        hit = pos[:1] in (["apply"], ["destroy"], ["import"]) or pos[:2] == ["state", "rm"]
    elif name == "pulumi":
        hit = positionals(args, {"-C", "--cwd", "-s", "--stack"})[:1] in (["up"], ["update"], ["destroy"])
    elif name == "kubectl":
        kpos = positionals(args, KUBE_ARGS)
        hit = bool(kpos) and kpos[0] in KUBE_WRITES and not (kpos[0] == "rollout" and kpos[1:2] in (["status"], ["history"]))
    elif name == "helm":
        hit = positionals(args, HELM_ARGS)[:1] in (["install"], ["upgrade"], ["uninstall"], ["rollback"], ["delete"])
    elif name == "vercel":
        hit = any(a.startswith("--prod") for a in args)
    elif name == "netlify":
        hit = pos[:1] == ["deploy"] and any(a.startswith("--prod") for a in args)
    elif name in ("fly", "flyctl"):
        hit = positionals(args, {"-a", "--app", "-c", "--config"})[:1] == ["deploy"]
    elif name == "wrangler":
        hit = bool({"deploy", "publish", "delete"} & set(pos))
    elif name == "cf":
        hit = pos[:1] == ["deploy"]
    elif name == "firebase":
        hit = positionals(args, {"--project", "-P"})[:1] == ["deploy"]
    elif name == "gcloud":
        hit = bool({"deploy", "delete"} & set(pos))
    elif name == "aws":
        hit = any(p.startswith("delete-") for p in pos) or bool(
            pairs & {("s3", "rm"), ("s3", "rb"), ("cloudformation", "deploy"), ("cloudformation", "delete-stack")})
    elif name == "supabase":
        hit = bool(pairs & {("db", "push"), ("db", "reset"), ("functions", "deploy")})
    elif name in ("npm", "pnpm", "yarn"):
        hit = "publish" in pos[:3] and "--dry-run" not in args
    elif name == "docker":
        dpos = positionals(args, {"--context", "-c", "-H", "--host", "--config", "-l", "--log-level"})
        hit = (dpos[:1] == ["push"] or dpos[:2] in (["image", "push"], ["compose", "push"])
               or (dpos[:1] == ["buildx"] and any(a == "--push" or a.startswith("--output=type=registry") for a in args)))
    elif name == "docker-compose":
        hit = pos[:1] == ["push"]
    elif name == "twine":
        hit = pos[:1] == ["upload"]
    elif name == "cargo":
        hit = [p for p in pos if not p.startswith("+")][:1] == ["publish"] and "--dry-run" not in args
    else:
        hit = False
    return EXTERNAL if hit else None


def in_place_flag(args, in_place_chars, stop_chars, long_flag=""):
    """True when a short option cluster sets in-place editing before an option that takes the rest of it."""
    for a in args:
        if a == "--":
            return False
        if long_flag and a.startswith(long_flag):
            return True
        if a.startswith("-") and not a.startswith("--"):
            j = 1
            while j < len(a):
                if a[j] in in_place_chars:
                    return True
                if a[j] in stop_chars:
                    break
                if a[j] in "0l":  # perl -0 and -l take optional digits
                    j += 1
                    while j < len(a) and a[j].isdigit():
                        j += 1
                    continue
                j += 1
    return False


def shell_write(name, args, writes, heredoc, bodies, cwd):
    """True when a factory subagent is writing a file from the shell instead of Edit/Write."""
    if heredoc:
        targets = writes + (positionals(args) if name == "tee" else [])
        if any(not safe_write_target(t, cwd) for t in targets):
            return True
    if name in ("sed", "gsed"):
        return in_place_flag(args, "iI", "efl", "--in-place")  # -I is BSD sed in-place
    if name == "perl":
        return in_place_flag(args, "i", "MmIdDxCeE")
    if PYTHON.fullmatch(name):
        codes = [args[k + 1] for k in range(len(args) - 1) if re.fullmatch(r"-[A-Za-z]*c", args[k])]
        if heredoc and not codes:
            codes = [body for body, _ in bodies]
        return any(PY_WRITE.search(code) for code in codes)
    return False


def unwrap(words, ctx, depth, findings):
    """Strip sudo, env, VAR=value, xargs, npx and similar so the real command comes first."""
    while words:
        head = os.path.basename(words[0])
        if head == "function":  # function NAME { body }: the body follows the name
            words = words[2:]
            continue
        if ASSIGNMENT.match(words[0]):
            words = words[1:]
            continue
        two_word = len(words) > 1 and (head, words[1]) in TWO_WORD_WRAPPERS
        if head not in WRAPPERS and not two_word:
            return words
        with_arg = TWO_WORD_ARGS if two_word else WRAPPERS[head]
        i = 2 if two_word else 1
        while i < len(words) and words[i].startswith("-") and words[i] != "-":
            if words[i] == "--":
                i += 1
                break
            opt, eq, value = words[i].partition("=")
            if opt in with_arg and not eq:
                value = words[i + 1] if i + 1 < len(words) else ""
                i += 2
            else:
                i += 1
            if opt in with_arg and opt in STRING_OPTS and value:
                findings.extend(scan(value, ctx, depth + 1))
        words = words[i:]
        if head == "timeout" and words:
            words = words[1:]  # the duration
    return words


def command_name(word):
    """Program name without its path or npx-style @version (wrangler@3 -> wrangler)."""
    name = os.path.basename(word)
    if "@" in name[1:]:
        name = name[:name.index("@", 1)]
    return CLI_ALIASES.get(name, name)


def check_words(words, writes, heredoc, bodies, ctx, depth, piped=False):
    findings = []
    words = unwrap(words, ctx, depth, findings)
    if not words:
        return findings
    cwd, subagent = ctx
    name, args = command_name(words[0]), words[1:]
    what = " ".join(words)
    first = (positionals(args)[:1] or [""])[0]
    unresolved = re.search(r"[$`]", words[0])
    if ((unresolved or (name not in ("rm", "sed", "perl") and re.search(r"[$`]", first))) and FALLBACK.search(what)) or (
            unresolved and RISKY.search(what)) or (name in ("git", "gh") and first.startswith("$")):
        findings.append(("ask", what[:120], UNPARSED))  # name or subcommand built at runtime
    if name in SHELLS:
        c_index = next((k for k, a in enumerate(args) if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a)), None)
        if c_index is not None:
            rest = [a for a in args[c_index + 1:] if not a.startswith("-")]
            if rest:
                findings.extend(scan(rest[0], ctx, depth + 1))
        elif heredoc:
            for body, _ in bodies:
                findings.extend(scan(body, ctx, depth + 1))
        elif piped and not positionals(args):
            findings.append(("ask", what, PIPED_SHELL))
    elif name == "eval":
        findings.extend(scan(" ".join(args), ctx, depth + 1))
    elif name == "find":
        for k, a in enumerate(args):
            if a in ("-exec", "-execdir", "-ok", "-okdir"):
                inner = []
                for b in args[k + 1:]:
                    if b in (";", "+"):
                        break
                    inner.append(b)
                findings.extend(check_words(inner, [], False, bodies, ctx, depth + 1))
    elif PYTHON.fullmatch(name) and "-m" in args:
        findings.extend(check_words(args[args.index("-m") + 1:], [], False, bodies, ctx, depth + 1))
    why = rule(name, args, cwd)
    if why:
        findings.append(("ask", what, why))
    if subagent and shell_write(name, args, writes, heredoc, bodies, cwd):
        findings.append(("deny", what, ""))
    return findings


def fallback(text):
    return [("ask", text.strip()[:120], UNPARSED)] if FALLBACK.search(text) else []


def scan(text, ctx, depth=0):
    """Findings (decision, what, why) for one piece of shell text."""
    if depth > MAX_DEPTH:
        return [("ask", text.strip()[:120], UNPARSED)]
    try:
        tokens, bodies, subs = lex(text)
    except ValueError:
        return fallback(text)
    findings = []
    for inner in subs:
        findings.extend(scan(inner, ctx, depth + 1))
    for pipeline in pipelines(tokens):
        parts = [split_redirects(seg) for seg in pipeline]
        heredoc = any(h for _, _, h in parts)
        for k, (words, writes, _) in enumerate(parts):
            findings.extend(check_words(words, writes, heredoc, bodies, ctx, depth, piped=k > 0))
    return findings


def in_factory_project(cwd):
    return bool(factory_roots(cwd))


def decision(findings):
    """The hook output for these findings, or None."""
    denies = [f for f in findings if f[0] == "deny"]
    if denies:
        what = "; ".join(dict.fromkeys(f"`{w[:120]}`" for _, w, _ in denies))
        reason = (f"Software Factory gate: {what} writes a file from the shell. "
                  "Use the Edit or Write tool for file changes (contract rule 9.12).")
        kind = "deny"
    elif findings:
        what = "; ".join(dict.fromkeys(f"`{w[:120]}` is {why}" for _, w, why in findings))
        reason = f"Software Factory gate: {what}. Approve only if the user approved this exact action."
        kind = "ask"
    else:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": kind,
                                   "permissionDecisionReason": reason}}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return 0
    cwd = str(payload.get("cwd") or os.getcwd())
    prefix, _, name = str(payload.get("agent_type") or "").rpartition(":")
    factory = prefix in ("", "software-factory") and name in FACTORY_AGENTS
    if not factory and not in_factory_project(cwd):
        return 0
    # The Team Lead may be the main session; every other factory agent is a specialist subagent.
    subagent = factory and (bool(payload.get("agent_id")) or name != "team-lead")
    try:
        findings = scan(command, (cwd, subagent))
    except Exception:  # in scope, so an internal error fails toward asking
        findings = [("ask", command.strip()[:120], UNPARSED)]
    out = decision(findings)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
