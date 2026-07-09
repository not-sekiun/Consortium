#!/usr/bin/env python3
# Reflow over-long "#" comments so they respect a max line length.
#
# A run of consecutive, same-indent, same-hash-count full-line "#" comments
# is treated as one paragraph. If ANY line in that paragraph exceeds the
# limit, the whole paragraph is re-wrapped on whitespace, which naturally
# merges short trailing lines up into the freed space. Blocks that already
# fit are left untouched so intentional line breaks survive.
#
# Deliberately left alone: docstrings and any other string literals (a "#"
# inside a string is never a comment), inline/trailing comments, blank "#"
# separators, decorative "####" rules, and tooling directives such as
# "# type:", "# noqa", "# pragma", coding declarations, and shebangs.

import argparse
import difflib
import io
import os
import sys
import textwrap
import tokenize

# Prefixes (checked after stripping leading "#" and whitespace, lowercased)
# that mark a comment as machine-meaningful and therefore untouchable.
DIRECTIVE_PREFIXES = (
    "type:",
    "noqa",
    "pragma",
    "pylint:",
    "mypy:",
    "flake8:",
    "fmt:",
    "yapf:",
    "isort:",
    "nosec",
    "coding:",
    "coding=",
)

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".tox",
    ".pytest_cache",
    "build",
    "dist",
}


def split_comment(s):
    # Return (hash_count, text) for a raw comment token like "## hello".
    # text is stripped of the marker and surrounding whitespace.
    stripped = s.lstrip("#")
    hashes = len(s) - len(stripped)
    return hashes, stripped.strip()


def is_directive(raw, row):
    # raw is the full comment token including its leading "#"(s).
    if raw.startswith("#!"):
        return True
    if "-*-" in raw:
        return True
    low = raw.lstrip("#").strip().lower()
    return any(low.startswith(p) for p in DIRECTIVE_PREFIXES)


def find_standalone_comments(source, lines):
    # Map 1-based row -> (col, hashes, text, is_directive, is_blank) for
    # every full-line comment. Returns None if the source won't tokenize.
    src = source if source.endswith("\n") else source + "\n"
    found = {}
    try:
        tokens = tokenize.generate_tokens(io.StringIO(src).readline)
        for tok in tokens:
            if tok.type != tokenize.COMMENT:
                continue
            row, col = tok.start
            # A comment is "standalone" only if nothing but whitespace
            # precedes it on its line; otherwise it's an inline comment.
            if lines[row - 1][:col].strip() != "":
                continue
            hashes, text = split_comment(tok.string)
            found[row] = (col, hashes, text, is_directive(tok.string, row), text == "")
    except tokenize.TokenError:
        return None
    except SyntaxError:
        # IndentationError is a SyntaxError subclass, so this covers it.
        return None
    return found


def group_blocks(standalone):
    # Group reflowable rows into blocks of consecutive rows sharing the
    # same indent column and hash count.
    reflowable = [
        r for r in sorted(standalone) if not standalone[r][3] and not standalone[r][4]
    ]
    blocks, cur = [], []
    for r in reflowable:
        if cur:
            pcol, phash = standalone[cur[-1]][0], standalone[cur[-1]][1]
            contiguous = (
                r == cur[-1] + 1
                and standalone[r][0] == pcol
                and standalone[r][1] == phash
            )
            if not contiguous:
                blocks.append(cur)
                cur = []
        cur.append(r)
    if cur:
        blocks.append(cur)
    return blocks


def reflow_source(source, max_len):
    # Return (new_source, changed). Pure text-in/text-out; the CLI wraps
    # file handling around this so it's trivially testable.
    had_final_nl = source.endswith("\n")
    lines = source.split("\n")
    if had_final_nl:
        lines = lines[:-1]

    standalone = find_standalone_comments(source, lines)
    if standalone is None:
        return source, False

    replace, skip, changed = {}, set(), False
    for block in group_blocks(standalone):
        if not any(len(lines[r - 1]) > max_len for r in block):
            continue
        col, hashes = standalone[block[0]][0], standalone[block[0]][1]
        indent = lines[block[0] - 1][:col]
        marker = "#" * hashes + " "
        width = max_len - len(indent) - len(marker)
        if width < 1:
            # No room to wrap (indent deeper than the limit); leave as-is.
            continue
        # Flatten to words so any internal whitespace runs collapse to
        # single spaces on output.
        text = " ".join(w for r in block for w in standalone[r][2].split())
        wrapped = textwrap.wrap(
            text, width=width, break_long_words=False, break_on_hyphens=False
        )
        new_lines = [indent + marker + w for w in wrapped]
        if new_lines != [lines[r - 1] for r in block]:
            changed = True
        replace[block[0]] = new_lines
        for r in block[1:]:
            skip.add(r)

    if not changed:
        return source, False

    out = []
    for i, line in enumerate(lines, 1):
        if i in skip:
            continue
        if i in replace:
            out.extend(replace[i])
        else:
            out.append(line)
    new_source = "\n".join(out)
    if had_final_nl:
        new_source += "\n"
    return new_source, True


def iter_files(root, extensions, excludes):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes]
        for name in filenames:
            if os.path.splitext(name)[1] in extensions:
                yield os.path.join(dirpath, name)


RED, GREEN, CYAN, BOLD, RESET = "\033[31m", "\033[32m", "\033[36m", "\033[1m", "\033[0m"


def colorize_diff(diff_lines):
    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            yield BOLD + line + RESET
        elif line.startswith("@@"):
            yield CYAN + line + RESET
        elif line.startswith("+"):
            yield GREEN + line + RESET
        elif line.startswith("-"):
            yield RED + line + RESET
        else:
            yield line


def process_file(path, max_len, in_place, show_diff, color):
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except (UnicodeDecodeError, OSError) as e:
        print(f"skip {path}: {e}", file=sys.stderr)
        return False

    new_source, changed = reflow_source(source, max_len)
    if not changed:
        return False

    if show_diff:
        diff = difflib.unified_diff(
            source.splitlines(),
            new_source.splitlines(),
            fromfile=path,
            tofile=path,
            lineterm="",
        )
        if color:
            diff = colorize_diff(diff)
        print("\n".join(diff))
    if in_place:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_source)
    return True


def build_parser():
    p = argparse.ArgumentParser(
        description="Reflow over-long '#' comments to a max line length, "
        "merging short follow-on lines. Docstrings, string "
        "literals, inline comments and directives are ignored."
    )
    p.add_argument("path", help="File or directory to process.")
    p.add_argument(
        "-l",
        "--max-line-length",
        type=int,
        default=88,
        help="Maximum line length (default: 88).",
    )
    p.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Rewrite files. Default is a dry run.",
    )
    p.add_argument(
        "-e",
        "--extensions",
        default=".py",
        help="Comma-separated extensions to scan (default: .py).",
    )
    p.add_argument(
        "-x",
        "--exclude",
        default="",
        help="Comma-separated extra directory names to skip.",
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress the per-file diff output."
    )
    p.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Colorize diff output (default: auto).",
    )
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    extensions = {
        e if e.startswith(".") else "." + e for e in args.extensions.split(",") if e
    }
    excludes = DEFAULT_EXCLUDES | {d for d in args.exclude.split(",") if d}
    show_diff = not args.quiet
    color = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())

    changed_files = 0
    for path in iter_files(args.path, extensions, excludes):
        if process_file(path, args.max_line_length, args.in_place, show_diff, color):
            changed_files += 1

    verb = "rewrote" if args.in_place else "would change"
    print(f"\n{verb} {changed_files} file(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
