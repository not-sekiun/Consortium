#!/usr/bin/env python3
"""
add_license_header.py

Walks a source directory recursively, finds *.py files (respecting
.gitignore via `git ls-files`), and inserts a license header as line
comments (# ...) at the top of each file -- not as a docstring.

Idempotent: if the header is already present, the file is left alone.
Designed to be run as a pre-commit hook.

Usage:
    python add_license_header.py --source-dir . --license-file LICENSE_HEADER.txt

Exit codes:
    0 - nothing changed
    1 - one or more files were modified (so pre-commit fails the run,
        forcing you to `git add` the changes and re-commit)
    2 - error (e.g. license file missing, not a git repo)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_COMMENT_PREFIX = "#"
# Marker used to detect an already-inserted header. We use the first
# non-blank line of the rendered comment block, so as long as that line
# is stable/unique, re-runs won't duplicate the header.
MARKER_PREFIX = "# ---- LICENSE HEADER"


def get_tracked_and_untracked_py_files(source_dir: Path) -> list[Path]:
    """
    Return all *.py files under source_dir that git would NOT ignore,
    using git's own .gitignore resolution (handles nested .gitignore,
    global excludes, etc. correctly).
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(source_dir),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "*.py",
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print("error: git executable not found on PATH", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        print(f"error: git ls-files failed: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(2)

    raw = result.stdout.decode("utf-8", errors="replace")
    if not raw:
        return []

    files = [source_dir / p for p in raw.split("\0") if p]
    return sorted(f for f in files if f.is_file())


def build_comment_block(license_text: str, comment_prefix: str) -> str:
    """
    Render the license text as a block of line comments, wrapped with a
    marker line so future runs can detect it.
    """
    lines = license_text.rstrip("\n").split("\n")
    commented = []
    for line in lines:
        if line.strip():
            commented.append(f"{comment_prefix} {line}")
        else:
            commented.append(comment_prefix)  # avoid trailing whitespace on blank lines

    block = [MARKER_PREFIX + " " + "-" * 8]
    block.extend(commented)
    block.append(comment_prefix + " " + "-" * (len(MARKER_PREFIX) + 9 - 2))
    return "\n".join(block) + "\n"


def already_has_header(content: str) -> bool:
    return MARKER_PREFIX in content


def insert_header(content: str, header_block: str) -> str:
    """
    Insert header_block at the top of content, but after a shebang line
    and/or a PEP 263 coding declaration if present, since those must
    stay on the first one or two lines to be effective.
    """
    lines = content.split("\n")
    insert_at = 0

    if lines and lines[0].startswith("#!"):
        insert_at = 1
        # PEP 263 coding declaration must be on line 1 or 2
        if len(lines) > 1 and _is_coding_line(lines[1]):
            insert_at = 2
    elif lines and _is_coding_line(lines[0]):
        insert_at = 1

    before = "\n".join(lines[:insert_at])
    after = "\n".join(lines[insert_at:])

    pieces = []
    if before:
        pieces.append(before)
    pieces.append(header_block.rstrip("\n"))
    pieces.append(after)

    result = "\n".join(pieces)
    if not result.endswith("\n"):
        result += "\n"
    return result


def _is_coding_line(line: str) -> bool:
    return line.startswith("#") and ("coding:" in line or "coding=" in line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("."),
        help="Root directory to search (must be inside a git repo). Default: cwd",
    )
    parser.add_argument(
        "--license-file",
        type=Path,
        required=True,
        help="Path to a text file containing the license header text (plain text, no comment chars)",
    )
    parser.add_argument(
        "--comment-prefix",
        default=DEFAULT_COMMENT_PREFIX,
        help="Comment prefix to use, default '#'",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional explicit list of files (as pre-commit passes staged files). "
        "If omitted, all tracked/untracked-but-not-ignored *.py files under --source-dir are used.",
    )
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()

    if not args.license_file.is_file():
        print(f"error: license file not found: {args.license_file}", file=sys.stderr)
        return 2
    license_text = args.license_file.read_text(encoding="utf-8")

    if args.files:
        # pre-commit typically passes the staged filenames directly.
        target_files = [Path(f).resolve() for f in args.files if f.endswith(".py")]
    else:
        target_files = get_tracked_and_untracked_py_files(source_dir)

    header_block = build_comment_block(license_text, args.comment_prefix)

    changed: list[Path] = []
    for path in target_files:
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue

        if already_has_header(content):
            continue

        new_content = insert_header(content, header_block)
        path.write_text(new_content, encoding="utf-8")
        changed.append(path)

    if changed:
        print("Inserted license header into:")
        for p in changed:
            try:
                rel = p.relative_to(source_dir)
            except ValueError:
                rel = p
            print(f"  {rel}")
        return 1  # signal pre-commit that files were modified

    print("License headers already present in all files. Nothing to do.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
