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

import argparse
import json
import os
import sys


def merge_ranges(ranges):
    """Sort and merge overlapping/adjacent (start, end) ranges."""
    ranges = sorted(ranges, key=lambda r: r[0])
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def trim(input_path, ranges, output_path):
    for start, end in ranges:
        if end <= start:
            raise ValueError(f"end must be greater than start (got {start}, {end})")

    ranges = merge_ranges(ranges)

    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("empty cast file")

    header = lines[0]  # header line is passed through unchanged
    out_lines = [header]

    kept = 0
    dropped = 0
    range_idx = 0
    cum_shift = 0.0

    for line in lines[1:]:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        ts, kind, data = json.loads(line)

        # Advance past any ranges fully behind this timestamp, accumulating shift.
        while range_idx < len(ranges) and ts >= ranges[range_idx][1]:
            r_start, r_end = ranges[range_idx]
            cum_shift += r_end - r_start
            range_idx += 1

        if (
            range_idx < len(ranges)
            and ranges[range_idx][0] <= ts < ranges[range_idx][1]
        ):
            dropped += 1
            continue

        ts -= cum_shift
        out_lines.append(json.dumps([round(ts, 6), kind, data]) + "\n")
        kept += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    total_cut = sum(end - start for start, end in ranges)
    print(f"cut {len(ranges)} range(s), total {total_cut:.3f}s removed")
    print(f"kept {kept} events, dropped {dropped} events")
    print(f"wrote {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Cut one or more time ranges out of an asciinema .cast file.",
    )
    parser.add_argument("input", help="input .cast file")
    parser.add_argument(
        "times",
        nargs="+",
        type=float,
        help="pairs of start end start end ... (must be an even count)",
    )
    parser.add_argument("-o", "--output", default=None, help="output .cast file")
    args = parser.parse_args()

    if len(args.times) % 2 != 0:
        parser.error("times must be given in start/end pairs (even count)")

    ranges = list(zip(args.times[0::2], args.times[1::2], strict=True))

    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_trimmed{ext}"

    try:
        trim(args.input, ranges, output_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
