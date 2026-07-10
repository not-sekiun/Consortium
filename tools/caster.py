#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pexpect",
# ]
# ///
"""
caster - record scripted terminal sessions to asciinema .cast files.

Usage:
    python caster.py demo.tape

Tape file syntax (VHS-inspired):

    # Comments start with '#'
    Output demo.cast              # where to save the recording (default: <tape>.cast)
    Set Shell /bin/bash           # what to spawn (default: $SHELL or /bin/bash)
    Set TypingSpeed 0.05          # global per-character delay in seconds (float)

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

Notes:
- Type does NOT press Enter for you; use an explicit Enter line.
- Everything runs inside one spawned shell, so `Type "my-repl"` + Enter
  drops you into your REPL and subsequent lines are typed into it.
- The tool re-launches itself under `asciinema rec` automatically.
- Progress ("line N: <content>") is printed to YOUR terminal's stderr as
  each tape line executes, and is kept OUT of the recording.
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

TYPE_RE = re.compile(r"^Type(?:@(?P<speed>[0-9]*\.?[0-9]+)s?)?\s+(?P<text>.*)$")
SLEEP_RE = re.compile(r"^Sleep\s+(?P<secs>[0-9]*\.?[0-9]+)s?$")
SET_RE = re.compile(r"^Set\s+(?P<key>\w+)\s+(?P<value>.+)$")
OUTPUT_RE = re.compile(r"^Output\s+(?P<path>.+)$")

STATUS_ENV = "CASTER_STATUS_FILE"
INNER_FLAG = "--_inner"


class TapeError(Exception):
    pass


def _unquote(text):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def parse_tape(path):
    """Parse a tape file into (settings, actions).

    settings: dict with 'output', 'shell', 'typing_speed'
    actions:  list of dicts. Every action carries 'lineno' and 'raw'
              (the original tape line) for progress reporting, plus:
                {'op': 'type',  'text': str, 'speed': float|None}
                {'op': 'sleep', 'secs': float}
                {'op': 'key',   'key': 'enter'|'tab'|'space'}
    """
    settings = {
        "output": None,
        "shell": os.environ.get("SHELL", "/bin/bash"),
        "typing_speed": 0.05,
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
                actions.append({**base, "op": "key", "key": line.lower()})
                continue

            raise TapeError(f"line {lineno}: cannot parse {line!r}")

    if settings["output"] is None:
        base_name, _ = os.path.splitext(path)
        settings["output"] = base_name + ".cast"
    return settings, actions


# ---------------------------------------------------------------------------
# Execution (runs inside asciinema)
# ---------------------------------------------------------------------------

KEYS = {
    "enter": "\r",
    "tab": "\t",
    "space": " ",
}


def run_tape(settings, actions):
    import pexpect  # imported here so parse errors surface before dependency errors

    status_path = os.environ.get(STATUS_ENV)
    status_file = open(status_path, "a", encoding="utf-8") if status_path else None

    def report(action):
        if status_file is not None:
            status_file.write(f"line {action['lineno']}: {action['raw']}\n")
            status_file.flush()

    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    child = pexpect.spawn(
        settings["shell"],
        encoding="utf-8",
        dimensions=(rows, cols),
        echo=True,
    )
    # Mirror everything the pty produces (which includes echoed keystrokes)
    # to our stdout, which asciinema is recording.
    child.logfile_read = sys.stdout

    # Give the shell a moment to print its prompt.
    time.sleep(0.5)

    def type_text(text, speed):
        for ch in text:
            child.send(ch)
            time.sleep(speed)

    try:
        for action in actions:
            report(action)
            if action["op"] == "sleep":
                time.sleep(action["secs"])
            elif action["op"] == "type":
                speed = action["speed"]
                type_text(
                    action["text"],
                    speed if speed is not None else settings["typing_speed"],
                )
            elif action["op"] == "key":
                child.send(KEYS[action["key"]])
                time.sleep(0.05)  # tiny settle so echoes land in order
        # Drain remaining output briefly, then shut down.
        time.sleep(0.5)
        child.sendline("exit")
        child.expect(pexpect.EOF, timeout=10)
    except pexpect.exceptions.ExceptionPexpect:
        pass
    finally:
        if child.isalive():
            child.close(force=True)
        if status_file is not None:
            status_file.write("done\n")
            status_file.flush()
            status_file.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _tail_status(status_path, proc):
    """Stream progress lines from the status file to OUR stderr while
    asciinema runs. This output never enters the recording because it is
    written by the outer process, outside the recorded pty."""
    with open(status_path, encoding="utf-8") as sf:
        while True:
            line = sf.readline()
            if line:
                print(f"[caster] {line}", end="", file=sys.stderr, flush=True)
                continue
            if proc.poll() is not None:
                # Process exited; drain anything left, then stop.
                remainder = sf.read()
                if remainder:
                    for rline in remainder.splitlines():
                        print(f"[caster] {rline}", file=sys.stderr, flush=True)
                return
            time.sleep(0.05)


def main():
    args = list(sys.argv[1:])
    inner = INNER_FLAG in args
    if inner:
        args.remove(INNER_FLAG)

    if len(args) != 1:
        print(f"usage: {os.path.basename(sys.argv[0])} <tape-file>", file=sys.stderr)
        sys.exit(2)

    tape_path = args[0]
    try:
        settings, actions = parse_tape(tape_path)
    except (TapeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if inner:
        run_tape(settings, actions)
        return

    # Outer invocation: wrap ourselves in asciinema rec.
    if shutil.which("asciinema") is None:
        print("error: asciinema not found on PATH", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(
        mode="w", prefix="caster-status-", suffix=".log", delete=False
    ) as tf:
        status_path = tf.name

    inner_cmd = shlex.join(
        [sys.executable, os.path.abspath(__file__), INNER_FLAG, tape_path]
    )
    env = {**os.environ, STATUS_ENV: status_path}
    proc = subprocess.Popen(
        ["asciinema", "rec", "--overwrite", "-c", inner_cmd, settings["output"]],
        env=env,
    )
    try:
        _tail_status(status_path, proc)
        proc.wait()
    finally:
        try:
            os.unlink(status_path)
        except OSError:
            pass
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
