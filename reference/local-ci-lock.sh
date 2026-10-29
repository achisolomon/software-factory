#!/bin/sh
# Machine-wide lock for a local CI script whose tests bind fixed ports (emulators, a dev server).
# Parallel sessions or worktrees on one machine queue behind each other for the port phase instead of colliding.
# Source: pushapp web scripts/ci-local.sh, https://github.com/Pushapp-Team/web/pull/357 (2026-10-29).
#
# Use in the project's local CI script:
#   LOCK=/tmp/<project>-ci-local-lock      # fixed path, see below
#   PORTS="8080 9099 3000"                 # every fixed port the locked phase uses
#   LOGS="${TMPDIR:-/tmp}/ci-local-logs/$(basename "$PWD")"   # one log folder per worktree
#   . scripts/local-ci-lock.sh             # a copy of this file in the project, or paste the two functions
#   <typecheck, lint, unit tests: no ports, stay parallel>
#   take_lock
#   <emulator tests, build, browser tests: hold the lock until the script exits>
#
# Gotchas:
# - LOCK is under /tmp, not $TMPDIR: Claude Code gives each session its own TMPDIR, so a lock there is never shared.
# - The lock is a symlink to "pid:worktree": ln -s creates it and records the owner in one atomic step, so a crash
#   never leaves an ownerless lock (a mkdir plus pid file has that gap).
# - ps is blocked in the Claude Code sandbox; a ps check makes a live holder look dead. Use kill -0 and treat only
#   "No such process" as dead (a denied signal means alive).
# - nc -z works in the sandbox. Check 127.0.0.1 and ::1: nc -z localhost alone misses a server on the other family.
# - Test the port check with nc -lk, not nc -l: a plain listener exits after the first probe, so the retry sees a free
#   port and the check looks broken.
# - Tests that spawn tsx fail inside the sandbox (listen EPERM on its IPC pipe): run local CI with the sandbox off.
# - The lock only queues runs of this script. A playground, pre-push hook or manual run can still hold the ports,
#   so the port check after the lock fails with a clear message instead of waiting forever.
# - Separate ports per worktree is the alternative only when no port is fixed by outside config (OAuth origins etc.).
# - Accepted limits: no wait timeout, no PID-reuse guard, a microsecond take-over race (the port check is the backstop).

ME="$$:$PWD"

release_lock() { [ "$(readlink "$LOCK" 2>/dev/null)" = "$ME" ] && rm -f "$LOCK"; return 0; }

take_lock() {
    waiting=0
    while ! ln -s "$ME" "$LOCK" 2>/dev/null; do
        holder=$(readlink "$LOCK" 2>/dev/null || true)
        [ -n "$holder" ] || continue
        if kill -0 "${holder%%:*}" 2>&1 | grep -qi 'no such process'; then
            # Re-read right before removing, so a lock another waiter just took over is not deleted.
            [ "$(readlink "$LOCK" 2>/dev/null)" = "$holder" ] && rm -f "$LOCK"
            continue
        fi
        [ "$waiting" -eq 1 ] || echo "waiting for ports $PORTS, held by: ${holder#*:}"
        waiting=1
        sleep 10
    done
    trap release_lock EXIT
    trap 'exit 130' INT TERM
    # Up to 15 s per port: the previous holder's servers may still be shutting down.
    for port in $PORTS; do
        tries=0
        while nc -z 127.0.0.1 "$port" 2>/dev/null || nc -z ::1 "$port" 2>/dev/null; do
            tries=$((tries + 1))
            if [ "$tries" -ge 15 ]; then
                echo "port $port is busy outside this lock (a playground, a pre-push run or a manual server?): stop it, then run again"
                exit 1
            fi
            sleep 1
        done
    done
}
