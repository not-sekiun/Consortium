#!/usr/bin/env python3
"""
asciinema_cast_trimmer.py - cut a time range out of an asciinema v2 .cast file.

Removes all events with timestamp in [start, end), and shifts every
event after `end` back by (end - start) seconds, so playback timing
stays correct with no dead gap.

Usage:
    python asciinema_cast_trimmer.py input.cast start end [output.cast]

Example:
    # cut out the 0.8s - 5.9s "Connecting to server..." spinner
    python asciinema_cast_trimmer.py demo.cast 0.8 5.9 demo_trimmed.cast

If output.cast is omitted, writes to <input>_trimmed.cast
"""

import json
import os
import sys


def trim(input_path, start, end, output_path):
    if end <= start:
        raise ValueError("end must be greater than start")
    duration = end - start

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("empty cast file")

    header = lines[0]  # header line is passed through unchanged
    out_lines = [header]

    kept = 0
    dropped = 0

    for line in lines[1:]:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        ts, kind, data = json.loads(line)

        if start <= ts < end:
            dropped += 1
            continue

        if ts >= end:
            ts -= duration

        out_lines.append(json.dumps([round(ts, 6), kind, data]) + "\n")
        kept += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"kept {kept} events, dropped {dropped} events, "
          f"shifted later events back by {duration:.3f}s")
    print(f"wrote {output_path}")


def main():
    if len(sys.argv) not in (4, 5):
        print(f"usage: {os.path.basename(sys.argv[0])} input.cast start end [output.cast]",
              file=sys.stderr)
        sys.exit(2)

    input_path = sys.argv[1]
    start = float(sys.argv[2])
    end = float(sys.argv[3])

    if len(sys.argv) == 5:
        output_path = sys.argv[4]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_trimmed{ext}"

    trim(input_path, start, end, output_path)


if __name__ == "__main__":
    main()
