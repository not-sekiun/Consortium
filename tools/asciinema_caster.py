#!/usr/bin/env python3
"""
caster - record scripted terminal sessions to asciinema .cast files.

Usage:
    python asciinema_caster.py demo.tape

Requires: tmux, asciinema. No Python dependencies.

Tape file syntax (VHS-inspired):

    # Comments start with '#'
    Output demo.cast              # where to save the recording (default: <tape>.cast)
    Set Shell /bin/bash           # what to spawn (default: $SHELL or /bin/bash)
    Set TypingSpeed 0.05          # global per-character delay in seconds (float)
    Set IdleTimeLimit 2           # cap any recorded idle gap to N seconds (float, optional)
    Set Cols 120                  # recorded terminal width in columns (default: 120)
    Set Rows 30                   # recorded terminal height in rows (default: 30)

    Type "uv run consortium.py client"   # typed at global speed, quotes optional
    Enter
    Sleep 12                      # seconds, float; trailing 's' allowed (12s)

    Type@0.1 connect              # per-line speed override (0.1s per char)
    Sleep 5s
    Enter

    Type@0.1 interact
    Space
    Tab
    Enter
    Sleep 2

How it works:
    caster starts a detached tmux session running `asciinema rec`, then
    injects keystrokes into it with `tmux send-keys`. Because tmux is a
    real terminal emulator, TUI apps (prompt_toolkit, spinners, cursor
    queries / CPR) work exactly as they would interactively.

    Progress is printed to caster's own terminal as each tape line runs,
    and you can watch the session live from another terminal with:

        tmux attach -r -t <session-name>   # printed at startup
"""

import os
import re
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

TYPE_RE = re.compile(r"^Type(?:@(?P<speed>[0-9]*\.?[0-9]+)s?)?\s+(?P<text>.*)$")
SLEEP_RE = re.compile(r"^Sleep\s+(?P<secs>[0-9]*\.?[0-9]+)s?$")
SET_RE = re.compile(r"^Set\s+(?P<key>\w+)\s+(?P<value>.+)$")
OUTPUT_RE = re.compile(r"^Output\s+(?P<path>.+)$")


class TapeError(Exception):
    pass


def _unquote(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def parse_tape(path):
    """Parse a tape file into (settings, actions).

    Every action dict carries 'lineno' and 'raw' (the original tape line)
    for progress reporting, plus:
        {'op': 'type',  'text': str, 'speed': float|None}
        {'op': 'sleep', 'secs': float}
        {'op': 'key',   'key': 'Enter'|'Tab'|'Space'}
    """
    settings = {
        "output": None,
        "shell": os.environ.get("SHELL", "/bin/bash"),
        "typing_speed": 0.05,
        "idle_time_limit": None,
        "cols": 120,
        "rows": 30,
    }
    actions = []

    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            base = {"lineno": lineno, "raw": line}

            if m := OUTPUT_RE.match(line):
                settings["output"] = _unquote(m.group("path"))
                continue

            if m := SET_RE.match(line):
                key = m.group("key").lower()
                value = _unquote(m.group("value"))
                if key == "typingspeed":
                    try:
                        settings["typing_speed"] = float(value.rstrip("s"))
                    except ValueError:
                        raise TapeError(
                            f"line {lineno}: bad TypingSpeed {value!r}"
                        ) from None
                elif key == "shell":
                    settings["shell"] = value
                elif key == "idletimelimit":
                    try:
                        settings["idle_time_limit"] = float(value.rstrip("s"))
                    except ValueError:
                        raise TapeError(
                            f"line {lineno}: bad IdleTimeLimit {value!r}"
                        ) from None
                elif key == "cols":
                    try:
                        settings["cols"] = int(value)
                    except ValueError:
                        raise TapeError(f"line {lineno}: bad Cols {value!r}") from None
                elif key == "rows":
                    try:
                        settings["rows"] = int(value)
                    except ValueError:
                        raise TapeError(f"line {lineno}: bad Rows {value!r}") from None
                else:
                    raise TapeError(
                        f"line {lineno}: unknown setting {m.group('key')!r}"
                    )
                continue

            if m := SLEEP_RE.match(line):
                actions.append({**base, "op": "sleep", "secs": float(m.group("secs"))})
                continue

            if m := TYPE_RE.match(line):
                speed = m.group("speed")
                actions.append(
                    {
                        **base,
                        "op": "type",
                        "text": _unquote(m.group("text")),
                        "speed": float(speed) if speed else None,
                    }
                )
                continue

            if line in ("Enter", "Tab", "Space"):
                actions.append({**base, "op": "key", "key": line})
                continue

            raise TapeError(f"line {lineno}: cannot parse {line!r}")

    if settings["output"] is None:
        base_name, _ = os.path.splitext(path)
        settings["output"] = base_name + ".cast"
    return settings, actions


# ---------------------------------------------------------------------------
# tmux driving
# ---------------------------------------------------------------------------


def tmux(*args, check=True):
    return subprocess.run(["tmux", *args], check=check, capture_output=True, text=True)


def session_alive(session):
    return tmux("has-session", "-t", session, check=False).returncode == 0


def progress(action):
    print(f"[caster] line {action['lineno']}: {action['raw']}", flush=True)


def run_tape(settings, actions, tape_path):
    session = f"caster-{os.getpid()}"
    cols, rows = settings["cols"], settings["rows"]

    idle_flag = ""
    if settings["idle_time_limit"] is not None:
        idle_flag = f"--idle-time-limit {settings['idle_time_limit']} "

    rec_cmd = (
        f"asciinema rec -q --overwrite "
        f"{idle_flag}"
        f"-c {shell_quote(settings['shell'])} "
        f"{shell_quote(settings['output'])}"
    )
    tmux(
        "new-session",
        "-d",
        "-s",
        session,
        "-x",
        str(cols),
        "-y",
        str(rows),
        rec_cmd,
    )
    print(f"[caster] recording '{tape_path}' -> {settings['output']}")
    print(f"[caster] watch live from another terminal:  tmux attach -r -t {session}")

    # Give asciinema + the shell a moment to come up.
    time.sleep(0.7)

    def send_literal(text):
        # -l = literal, '--' guards against text starting with '-'
        tmux("send-keys", "-t", session, "-l", "--", text)

    def send_key(name):  # Enter / Tab / Space
        tmux("send-keys", "-t", session, name)

    try:
        for action in actions:
            if not session_alive(session):
                print("[caster] session ended unexpectedly; stopping.", file=sys.stderr)
                return 1
            progress(action)
            if action["op"] == "sleep":
                time.sleep(action["secs"])
            elif action["op"] == "type":
                speed = action["speed"]
                speed = speed if speed is not None else settings["typing_speed"]
                if speed == 0:
                    # Instant: one write, appears all at once (like history recall).
                    send_literal(action["text"])
                else:
                    for ch in action["text"]:
                        send_literal(ch)
                        time.sleep(speed)
            elif action["op"] == "key":
                send_key(action["key"])
                time.sleep(0.05)

        # Wind down: exit the shell so asciinema finalizes the cast.
        time.sleep(0.5)
        if session_alive(session):
            send_literal("exit")
            send_key("Enter")

        # Wait for asciinema to finish writing.
        deadline = time.time() + 15
        while session_alive(session) and time.time() < deadline:
            time.sleep(0.1)
        if session_alive(session):
            print("[caster] session did not exit cleanly; killing it.", file=sys.stderr)
            tmux("kill-session", "-t", session, check=False)
            return 1

        print(f"[caster] done: {settings['output']}")
        return 0
    except KeyboardInterrupt:
        print("\n[caster] interrupted; killing session.", file=sys.stderr)
        tmux("kill-session", "-t", session, check=False)
        return 130


def shell_quote(s):
    import shlex

    return shlex.quote(s)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) != 2:
        print(f"usage: {os.path.basename(sys.argv[0])} <tape-file>", file=sys.stderr)
        sys.exit(2)

    for dep in ("tmux", "asciinema"):
        if shutil.which(dep) is None:
            print(f"error: {dep} not found on PATH", file=sys.stderr)
            sys.exit(1)

    tape_path = sys.argv[1]
    try:
        settings, actions = parse_tape(tape_path)
    except (TapeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(run_tape(settings, actions, tape_path))


if __name__ == "__main__":
    main()
