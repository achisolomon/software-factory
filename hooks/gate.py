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
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

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
    r"|\bdocker\b[^\n;&|]*\b(push|volume|prune|down)\b"
    r"|\b(psql|mysql|mariadb|mongosh|mongo|redis-cli|dropdb|mysqladmin|pg_restore|mongorestore)(?![\w.-])"
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
GH_READ_VERBS = {"list", "view", "status", "diff", "checks", "download", "watch", "get", "browse", "checkout"}
GH_READ_GROUPS = {"search", "browse", "status"}
ORIGIN = re.compile(r"(?:^|[@/])github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.I)
API_REPO = re.compile(r"/?repos/([^/]+)/([^/?#]+)")
API_URL = re.compile(r"https?://([^/]+)(/.*)?$", re.I)
HOOK_ENV = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "DATABASE_URL", "MYSQL_HOST", "GH_REPO", "DOCKER_HOST",
            "DOCKER_CONTEXT")
DOCKER_ARGS = {"--context", "-c", "-H", "--host", "--config", "-l", "--log-level", "-f", "--file", "-p",
               "--project-name", "--profile", "--env-file", "--project-directory", "-u", "--user", "-e", "--env",
               "-w", "--workdir"}
DB_STATEMENT_FLAGS = {"psql": ("-c", "--command"), "mysql": ("-e", "--execute"), "mariadb": ("-e", "--execute"),
                      "mongosh": ("--eval",), "mongo": ("--eval",), "redis-cli": (), "dropdb": (),
                      "mysqladmin": (), "pg_restore": (), "mongorestore": ()}
SSH_VALUE_FLAGS = {"-p", "-i", "-l", "-o", "-F", "-J", "-L", "-R", "-D", "-b", "-c", "-e", "-E", "-I", "-m", "-O",
                   "-Q", "-S", "-w", "-W", "-B"}
SSH_FLAG_CLUSTER = re.compile(r"-[46AaCfGgKkMNnqsTtVvXxYy]+[pilFJLRDbcEeIOQSwWBmo]")  # no-value letters, then one with
SSH_RUNS_COMMAND = re.compile(r"(?:remote|proxy|local)command\s*=", re.I)
NO_VALUE_FLAGS = "AtqXaEsS1"  # psql and mysql letters that take no value, so "-tAhHOST" still names a host
DB_VALUE_FLAGS = {"-U", "--username", "-p", "--port", "-u", "--user", "--password", "-P", "-a", "-n", "-f", "--file"}
REDIS_VALUE_FLAGS = DB_VALUE_FLAGS | {"-h", "--host", "-s", "-r", "-i", "-x", "--pass"}
REDIS_READS = {"GET", "MGET", "EXISTS", "TTL", "PTTL", "TYPE", "KEYS", "SCAN", "HGET", "HGETALL", "HMGET", "HKEYS",
               "HVALS", "HLEN", "LLEN", "LRANGE", "LINDEX", "SCARD", "SMEMBERS", "SISMEMBER", "ZCARD", "ZRANGE",
               "ZSCORE", "STRLEN", "DBSIZE", "INFO", "PING"}
DB_ENV = {"PGHOST", "PGHOSTADDR", "PGSERVICE", "DATABASE_URL", "MYSQL_HOST"}
DB_URI = re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss)://", re.I)
CONNINFO_HOST = re.compile(r"(?:^|\s)(?:host|hostaddr)\s*=\s*(\S+)")
AMBIGUOUS_HOST_FLAGS = re.compile(  # a short cluster with "h" that option_values skips; -pVALUE is a port or password
    rf"-(?![{NO_VALUE_FLAGS}]*h)(?!p)[^-]\w*h")
COMMENT = re.compile(r"/\*.*?\*/", re.S)
LOCAL_HOST = re.compile(r"localhost|[\w.-]*\.localhost|127(?:\.\d{1,3}){3}|::1", re.I)
DROP_DATABASE = re.compile(r"\bdrop\s+(?:database|schema)\b|dropDatabase", re.I)
SQL_READ_HEAD = re.compile(r"\s*(?:select|show|explain)\b|\s*\\", re.I)
SQL_WRITE_WORD = re.compile(
    r"\b(insert|update|delete|drop|truncate|alter|create|grant|revoke|merge|copy|call|do|into|outfile|analyze)\b", re.I)
SQL_READ_META = re.compile(r"\\(?:d[A-Za-z+]*|l\+?)(?![A-Za-z0-9_])")  # \d..., \l, \dt: describe and list only
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
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    scratch = os.path.join(project, ".software-factory-tmp") if project else None  # per-session folders from scratch.py
    for root in (os.environ.get("TMPDIR"), "/tmp", "/private/tmp", scratch):
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


def option_values(args, names):
    """Values of the options in names: "-h v", "-hv", "-tAhv" (after flags without values), "--host v", "--host=v"."""
    found = []
    for i, a in enumerate(args):
        following = args[i + 1] if i + 1 < len(args) else ""
        for name in names:
            if name.startswith("--"):
                if a == name:
                    found.append(following)
                elif a.startswith(name + "="):
                    found.append(a[len(name) + 1:])
            elif not a.startswith("--"):
                match = re.fullmatch(rf"-[{NO_VALUE_FLAGS}]*" + re.escape(name[1]) + r"(.*)", a, re.S)
                if match:
                    found.append(match.group(1) or following)
    return found


def repo_slug(value):
    """owner/name in lower case from "owner/name" or "github.com/owner/name", else None."""
    parts = value.lower().split("/")
    if len(parts) == 3 and parts[0] == "github.com":
        parts = parts[1:]
    return "/".join(parts) if len(parts) == 2 and all(re.fullmatch(r"[\w.-]+", p) for p in parts) else None


def effective_env(assigns):
    """The hook's own variables that matter here, overridden by the NAME=value words in front of the command."""
    env = {k: os.environ[k] for k in HOOK_ENV if os.environ.get(k)}
    for a in assigns:
        key, _, value = a.partition("=")
        env[key.rstrip("+")] = value
    return env


ORIGINS = {}  # path -> owner/name of its origin remote, or None; one hook run asks git at most once per path


def git_origin(path):
    if path not in ORIGINS:
        try:
            url = subprocess.run(["git", "-C", path, "remote", "get-url", "origin"], capture_output=True,
                                 text=True, timeout=2).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            url = ""
        match = ORIGIN.search(url)
        ORIGINS[path] = repo_slug("/".join(match.groups())) if match else None
    return ORIGINS[path]


def origin_slugs(cwd):
    """The repo(s) this session works on: the origin of cwd, else those of the factory projects at or below it."""
    if git_origin(cwd):
        return {git_origin(cwd)}
    return {slug for root in factory_roots(cwd) if (slug := git_origin(str(root)))}


def other_repo(value, cwd):
    """True unless value names the repo the session works on. An unreadable origin or odd name counts as other."""
    target = repo_slug(value)
    return not (target and target in origin_slugs(cwd))


def gh_repo_rule(args, pos, env, cwd):
    """EXTERNAL for a write that targets a repo other than the one the session works on (reads never ask)."""
    targets = option_values(args, ("-R", "--repo")) or ([env["GH_REPO"]] if env.get("GH_REPO") else [])
    if (targets and pos[1:2] and pos[1] not in GH_READ_VERBS and pos[0] not in GH_READ_GROUPS
            and any(other_repo(t, cwd) for t in targets)):
        return EXTERNAL
    return None


def gh_api_repo_rule(endpoint, method, env, cwd, hostname):
    """EXTERNAL for a non-GET call on another repo's endpoint. gh api has no -R flag: only the endpoint and GH_REPO."""
    if method == "GET":
        return None
    if hostname and hostname.lower() != "github.com":
        return EXTERNAL
    url = API_URL.match(endpoint)
    if url:
        if url.group(1).lower() not in ("api.github.com", "github.com"):
            return EXTERNAL
        endpoint = url.group(2) or ""
    endpoint = "/" + endpoint.lstrip("/")
    if ".." in endpoint.split("/") or "%" in endpoint or endpoint.startswith("/repositories/"):
        return EXTERNAL  # a path that is rewritten, encoded or addressed by id cannot be compared with the origin
    match = API_REPO.match(endpoint)
    if not match:
        return None
    # placeholders resolve to GH_REPO, else to the current repo
    target = env.get("GH_REPO") if match.groups() == ("{owner}", "{repo}") else "/".join(match.groups())
    return EXTERNAL if target and other_repo(target, cwd) else None


def gh_rule(args, env, cwd):
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
        endpoint = (positionals(rest, GH_API_ARGS) or [""])[0]
        if gh_api_repo_rule(endpoint, method, env, cwd, (option_values(rest, ("--hostname",)) or [""])[0]):
            return EXTERNAL
        if method in ("DELETE", "PUT", "PATCH"):
            return EXTERNAL
        if method == "POST":
            if endpoint == "graphql":
                return EXTERNAL if GRAPHQL_DESTRUCTIVE.search(" ".join(rest)) else None
            return None if "/issues" in "/" + endpoint.lstrip("/") else EXTERNAL
        return None
    if len(pos) >= 2 and pos[1] in GH_ASK.get(pos[0], ()):
        return EXTERNAL
    return gh_repo_rule(args, pos, env, cwd)


def bare_host(host):
    """Host without brackets or port: "[::1]:5432" -> "::1", "db:5432" -> "db"."""
    if host.startswith("["):
        return host[1:host.find("]")]
    return host.rsplit(":", 1)[0] if host.count(":") == 1 else host


def uri_hosts(uri):
    if uri.lower().startswith("mongodb+srv://"):
        return ["?"]  # the real hosts sit in DNS
    try:
        parts = urlsplit(uri)
    except ValueError:
        return ["?"]
    named = parse_qs(parts.query).get("host")
    netloc = named[0] if named else parts.netloc.rpartition("@")[2]
    return [bare_host(h) for h in netloc.split(",")]


def conn_hosts(arg):
    """Hosts named by a URI or a conninfo string; "?" when it cannot be read literally."""
    if DB_URI.match(arg):
        return uri_hosts(arg)
    if re.search(r"(?:^|\s)service=", arg):
        return ["?"]
    return [h.strip("'\"") for h in CONNINFO_HOST.findall(arg)]


def is_local_host(host):
    return host == "" or host.startswith("/") or bool(LOCAL_HOST.fullmatch(host))


def split_hosts(value):
    return [bare_host(h) for h in value.split(",") if h]


def db_remote(name, args, statements, env):
    """True when the DB client may reach a host that is not this machine. Ambiguous counts as remote."""
    if env.get("PGSERVICE") or option_values(args, ("--defaults-file", "--defaults-extra-file", "--login-path")):
        return True
    free = [a for a in args if a not in statements]  # statement text is not connection info
    hosts = [h for v in option_values(free, ("-h", "--host")) for h in split_hosts(v)]
    hosts += ["?" for a in free if AMBIGUOUS_HOST_FLAGS.match(a)]  # a cluster like -Uhenry may hide a host
    hosts += [h for a in free + option_values(free, ("-d", "--dbname")) for h in conn_hosts(a)]
    hosts += split_hosts(env.get("PGHOSTADDR", ""))  # libpq prefers it over any host name
    if not hosts and name != "redis-cli":
        words = positionals(free, DB_VALUE_FLAGS)
        hosts = ["?" for w in words if re.search(r"[$`]", w)]
        if name in ("mongosh", "mongo"):  # host/db, host:port/db or a dotted host; a bare word is a local database
            hosts += [bare_host(w.split("/")[0]) for w in words if re.search(r"[/:.]", w) and not w.endswith(".js")]
    if not hosts:
        hosts = split_hosts(env.get("PGHOST", "")) + split_hosts(env.get("MYSQL_HOST", ""))
        hosts += uri_hosts(env["DATABASE_URL"]) if env.get("DATABASE_URL") else []
    return not all(is_local_host(h) for h in hosts)


def sql_read_only(statement):
    parts = [p for p in statement.split(";") if p.strip()]
    return (bool(parts) and all(SQL_READ_HEAD.match(p) for p in parts) and not SQL_WRITE_WORD.search(statement)
            and "\\" not in SQL_READ_META.sub("", statement))


def db_rule(name, args, env, remote=False, text=""):
    """Why this database client call needs approval, or None. text is the whole command, for piped input."""
    if name == "dropdb" or (name == "mysqladmin" and "drop" in args):
        statements = ["DROP DATABASE"]
    elif name == "redis-cli":
        command = positionals(args, REDIS_VALUE_FLAGS)
        statements = [" ".join(command)] if command else []
    else:
        statements = option_values(args, DB_STATEMENT_FLAGS[name])
        if name == "psql" and option_values(args, ("-f", "--file")):
            statements = []  # a script file runs next to -c: judge it as unreadable
    # The read-only scan sees comments as written: MySQL runs /*! ... */ and a quoted '/*' hides nothing from it.
    if remote or db_remote(name, args, statements, env):
        if name in ("mongosh", "mongo") or not statements:
            return EXTERNAL  # eval strings and scripts can write in ways a keyword scan misses
        if name == "redis-cli":
            return None if statements[0].split()[0].upper() in REDIS_READS else EXTERNAL
        return None if all(sql_read_only(s) for s in statements) else EXTERNAL
    piped_drop = name in ("psql", "mysql", "mariadb") and not statements and DROP_DATABASE.search(COMMENT.sub(" ", text))
    return LOCAL if piped_drop or any(DROP_DATABASE.search(COMMENT.sub(" ", s)) for s in statements) else None


def db_client(args):
    """(name, args) of the first database client in args, also inside one quoted "psql -c ..." argument."""
    for i, a in enumerate(args):
        head = a.split(None, 1)[:1]
        if head and command_name(head[0]) in DB_STATEMENT_FLAGS:
            try:
                words = [w for w, is_op in lex(a)[0] if not is_op] if " " in a else [a]
            except ValueError:
                words = a.split()
            return command_name(words[0]), words[1:] + args[i + 1:]
    return None


def docker_rule(name, args):
    dpos = (["compose"] if name == "docker-compose" else []) + positionals(args, DOCKER_ARGS)
    if (dpos[:1] == ["push"] or dpos[:2] in (["image", "push"], ["compose", "push"])
            or (dpos[:1] == ["buildx"] and any(a == "--push" or a.startswith("--output=type=registry") for a in args))):
        return EXTERNAL
    volumes = any(a.startswith("--volumes") for a in args) or "v" in short_flags(args)
    if (dpos[:1] == ["volume"] and dpos[1:2] in (["rm"], ["remove"], ["prune"])
            or (dpos[:2] == ["system", "prune"] and any(a.startswith("--volumes") for a in args))
            or (dpos[:2] in (["compose", "down"], ["compose", "rm"], ["container", "rm"]) or dpos[:1] == ["rm"])
            and volumes):
        return LOCAL
    return None


def container_findings(args, env, what, ctx, depth):
    """A command started in a container (docker|compose exec|run). Remote when the docker daemon is not local."""
    index = next((k for k, a in enumerate(args) if a in ("exec", "run")), None)
    if index is None:
        return []
    cwd, subagent, state = ctx
    rest = args[index + 1:]
    remote = bool(state.get("remote") or option_values(args[:index], ("-H", "--host", "--context", "-c"))
                  or env.get("DOCKER_HOST") or env.get("DOCKER_CONTEXT"))
    client = db_client(rest)
    if client:  # the container's own environment is not ours: only its -e NAME=value pairs count
        inner = {k: v for k, _, v in (a.partition("=") for a in option_values(rest, ("-e", "--env"))) if k in HOOK_ENV}
        why = db_rule(*client, inner, remote=remote, text=state["text"])
        return [("ask", what, why)] if why else []
    shell = next((k for k, a in enumerate(rest) if command_name(a) in SHELLS), None)
    if shell is None:
        return []
    return check_words(rest[shell:], [], False, [], (cwd, subagent, {**state, "remote": remote}), depth + 1)


def ssh_parts(args):
    """(options, command text): the text ssh sends to the remote shell, which re-parses it ("ssh host cd x && psql")."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "--":
            i += 1
            break
        takes_value = args[i] in SSH_VALUE_FLAGS or SSH_FLAG_CLUSTER.fullmatch(args[i])  # -tp 2222: p takes 2222
        i += 2 if takes_value else 1
    rest = args[i + 1:]
    return args[:i], " ".join(rest[1:] if rest[:1] == ["--"] else rest)


def runner_findings(name, args, env, what, ctx, depth):
    """Findings for commands started on another machine or in a container: ssh, kubectl exec|run, docker exec|run."""
    cwd, subagent, state = ctx
    remote_ctx = (cwd, subagent, {**state, "remote": True})
    if name == "ssh":
        options, command = ssh_parts(args)
        found = scan(command, remote_ctx, depth + 1)
        if SSH_RUNS_COMMAND.search(" ".join(options)):  # these options run a command the gate cannot read
            found.append(("ask", what, UNPARSED))
        return found
    if name == "kubectl":
        if positionals(args, KUBE_ARGS)[:1] in (["exec"], ["run"]) and "--" in args:
            return check_words(args[args.index("--") + 1:], [], False, [], remote_ctx, depth + 1)
        return []
    return container_findings(args, env, what, ctx, depth)


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


def rule(name, args, cwd, assigns=(), state=None):
    """Why this command needs the user's approval, or None.

    assigns are the NAME=value words in front of the command. state["env_loaded"] is True when an earlier part of
    the same command exported, sourced or assigned database variables; state["remote"] when the command runs on
    another machine (ssh, kubectl exec); state["text"] is the whole command, for piped input.

    shortcut: the gate sees one Bash command, so it cannot see exports from the user's shell profile (each Bash
    call starts a fresh shell), ~/.pg_service.conf, ~/.my.cnf, .pgpass, `gh repo set-default` or fork resolution
    when -R is absent, or a SELECT that calls a side-effecting function (SELECT drop_everything(),
    SELECT pg_terminate_backend(...)), which passes as read-only on a remote host. Upgrade by asking for the
    resolved target first; SR-01 already makes the agent resolve targets before writing.
    """
    pos = positionals(args)
    pairs = set(zip(pos, pos[1:]))
    if name == "git":
        return git_rule(args)
    state = state or {}
    if name == "gh":
        return gh_rule(args, effective_env(assigns), cwd)
    if name == "rm":
        return rm_rule(args, cwd)
    if name in DB_STATEMENT_FLAGS:
        env = effective_env(assigns)
        if state.get("env_loaded"):
            env["PGSERVICE"] = "?"  # an earlier export or source may have set any variable: ambiguous
        return db_rule(name, args, env, remote=state.get("remote", False), text=state.get("text", ""))
    if name in ("docker", "docker-compose"):
        return docker_rule(name, args)
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
        hit = positionals(args, {"--project", "-P"})[:1] in (
            ["deploy"], ["firestore:delete"], ["database:remove"], ["functions:delete"], ["database:set"])
    elif name == "gcloud":
        hit = bool({"deploy", "delete"} & set(pos))
    elif name == "aws":
        hit = any(p.startswith("delete-") for p in pos) or bool(
            pairs & {("s3", "rm"), ("s3", "rb"), ("cloudformation", "deploy"), ("cloudformation", "delete-stack")})
    elif name == "supabase":
        hit = bool(pairs & {("db", "push"), ("db", "reset"), ("functions", "deploy")})
    elif name in ("npm", "pnpm", "yarn"):
        hit = "publish" in pos[:3] and "--dry-run" not in args
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
    """Strip sudo, env, VAR=value, xargs, npx and similar. Returns (the real command first, the NAME=value words)."""
    assigns = []
    while words:
        head = os.path.basename(words[0])
        if head == "function":  # function NAME { body }: the body follows the name
            words = words[2:]
            continue
        if ASSIGNMENT.match(words[0]):
            assigns.append(words[0])
            words = words[1:]
            continue
        two_word = len(words) > 1 and (head, words[1]) in TWO_WORD_WRAPPERS
        if head not in WRAPPERS and not two_word:
            return words, assigns
        with_arg = TWO_WORD_ARGS if two_word else WRAPPERS[head]
        i = 2 if two_word else 1
        while i < len(words) and words[i].startswith("-") and words[i] != "-":
            if words[i] == "--":
                i += 1
                break
            opt, eq, value = words[i].partition("=")
            if not eq and (opt in with_arg or (len(opt) > 2 and opt[1] != "-" and "-" + opt[-1] in with_arg)):
                value = words[i + 1] if i + 1 < len(words) else ""  # also a cluster ending in such an option: -iu
                i += 2
            else:
                i += 1
            if opt in with_arg and opt in STRING_OPTS and value:
                findings.extend(scan(value, ctx, depth + 1))
        words = words[i:]
        if head == "timeout" and words:
            words = words[1:]  # the duration
    return words, assigns


def command_name(word):
    """Program name without its path or npx-style @version (wrangler@3 -> wrangler)."""
    name = os.path.basename(word)
    if "@" in name[1:]:
        name = name[:name.index("@", 1)]
    return CLI_ALIASES.get(name, name)


def check_words(words, writes, heredoc, bodies, ctx, depth, piped=False):
    findings = []
    words, assigns = unwrap(words, ctx, depth, findings)
    cwd, subagent, state = ctx
    if not words:
        state["env_loaded"] |= any(a.partition("=")[0].rstrip("+") in DB_ENV for a in assigns)
        return findings
    name, args = command_name(words[0]), words[1:]
    env_loaded = state["env_loaded"]  # read before this command's own effect: it only matters for later commands
    if name in ("export", "source", ".") or (name == "set" and "a" in short_flags(args)):
        state["env_loaded"] = True
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
    if name in ("ssh", "kubectl", "docker", "docker-compose"):
        findings.extend(runner_findings(name, args, effective_env(assigns), what, ctx, depth))
    why = rule(name, args, cwd, assigns, {**state, "env_loaded": env_loaded})
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
    # Literal "deny" / "ask" only, never a variable: the plugin directory review must see this hook cannot approve.
    denies = [f for f in findings if f[0] == "deny"]
    if denies:
        what = "; ".join(dict.fromkeys(f"`{w[:120]}`" for _, w, _ in denies))
        reason = (f"Software Factory gate: {what} writes a file from the shell. "
                  "Use the Edit or Write tool for file changes (contract rule 9.12).")
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": reason}}
    if findings:
        what = "; ".join(dict.fromkeys(f"`{w[:120]}` is {why}" for _, w, why in findings))
        reason = f"Software Factory gate: {what}. Approve only if the user approved this exact action."
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                       "permissionDecisionReason": reason}}
    return None


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
        findings = scan(command, (cwd, subagent, {"env_loaded": False, "remote": False, "text": command}))
    except Exception:  # in scope, so an internal error fails toward asking
        findings = [("ask", command.strip()[:120], UNPARSED)]
    out = decision(findings)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
