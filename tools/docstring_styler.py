#!/usr/bin/env python3
"""
docstring_styler.py

Find multi-line triple-quoted docstrings in Python source files and report
or convert their "opening line" style.

Two styles are detected:

  "below" - text starts on the line AFTER the opening triple-quote
        \"\"\"
        Docstring text...
        \"\"\"

  "same"  - text starts on the SAME line as the opening triple-quote
        \"\"\"Docstring text...
        ...
        \"\"\"

Single-line docstrings (\"\"\"like this\"\"\") have no newline in them at all,
so they don't fall into either bucket and are always ignored.

USAGE
-----
Report only (no files are modified):
    python docstring_styler.py PATH [-r]

Convert everything found to one style, writing the files in place:
    python docstring_styler.py PATH [-r] --convert below
    python docstring_styler.py PATH [-r] --convert same

Preview a conversion as a unified diff without touching any files:
    python docstring_styler.py PATH [-r] --convert below --dry-run

PATH may be a single .py file or a directory. Use -r/--recursive to walk
subdirectories when PATH is a directory.

LIMITATIONS
-----------
- Only "real" docstrings are considered: the literal must be the first
  statement in the body of a module, class, function, or async function,
  and it must be a plain str literal (not an f-string -- those can't be
  docstrings anyway, since Python doesn't treat them as such).
- Implicitly concatenated string literals used as a docstring (e.g. two
  adjacent triple-quoted strings) are detected but skipped with a warning,
  since rewriting them safely isn't well-defined.
"""

import argparse
import ast
import difflib
import os
import re
import sys
from pathlib import Path

QUOTE_PREFIX_RE = re.compile(r'^([a-zA-Z]{0,2})("""|\'\'\')')

GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


def color_diff_line(line):
    """Color a single unified-diff line the standard way: file headers bold,
    hunk headers cyan, added lines green, removed lines red."""
    if line.startswith("+++") or line.startswith("---"):
        return BOLD + line + RESET
    if line.startswith("@@"):
        return CYAN + line + RESET
    if line.startswith("+"):
        return GREEN + line + RESET
    if line.startswith("-"):
        return RED + line + RESET
    return line


def use_color(choice):
    if choice == "always":
        return True
    if choice == "never":
        return False
    # 'auto'
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


class DocstringInfo:
    """Everything needed to inspect and rewrite a single docstring literal."""

    def __init__(self, start, end, raw, indent, owner_kind, owner_name, owner_lineno):
        self.start = start  # absolute char offset in the source string
        self.end = end  # absolute char offset (exclusive)
        self.raw = raw  # exact source text of the literal, incl. quotes
        self.indent = indent  # leading whitespace of the line the literal starts on
        self.owner_kind = owner_kind
        self.owner_name = owner_name
        self.owner_lineno = owner_lineno

        m = QUOTE_PREFIX_RE.match(raw)
        if not m:
            raise ValueError(f"unrecognized literal: {raw[:30]!r}")
        self.prefix = m.group(1)
        self.quote = m.group(2)
        self.inner = raw[m.end() : -3]

        # Safety check: a single literal should contain its triple-quote
        # sequence exactly twice (open + close). If it shows up again,
        # this is probably implicit string concatenation -- bail out
        # rather than risk corrupting it.
        if raw.count(self.quote) != 2:
            raise ValueError("looks like implicit string concatenation")

    @property
    def is_multiline(self):
        return "\n" in self.inner

    @property
    def style(self):
        first_line = self.inner.split("\n", 1)[0]
        return "below" if first_line.strip() == "" else "same"

    def converted(self, target):
        """Return the new raw literal text, converted to `target` style.

        `target` is 'below' or 'same'. Returns the original raw text
        unchanged if it's already in the target style.
        """
        if self.style == target:
            return self.raw

        lines = self.inner.split("\n")

        if target == "below":
            # same -> below: push the first line down onto its own line,
            # indented to match the rest of the docstring block.
            first_line = lines[0]
            rest = lines[1:]
            new_inner = "\n" + self.indent + first_line.strip()
            new_inner += ("\n" + "\n".join(rest)) if rest else ("\n" + self.indent)
        else:
            # below -> same: pull the first real content line up onto the
            # opening line; everything after it is left exactly as-is.
            content = lines[1] if len(lines) > 1 else ""
            rest = lines[2:]
            new_inner = content.lstrip()
            if rest:
                new_inner += "\n" + "\n".join(rest)

        return self.prefix + self.quote + new_inner + self.quote


def _line_offsets(text):
    """List mapping line number (1-indexed) -> absolute char offset of its start."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _owner_name(node):
    if isinstance(node, ast.Module):
        return "<module>"
    return node.name


def find_docstrings(source, path_for_warnings=None):
    """Parse `source` and return a list of DocstringInfo, sorted by position."""
    tree = ast.parse(source)
    offsets = _line_offsets(source)
    src_lines = source.splitlines()

    def to_offset(lineno, col):
        return offsets[lineno - 1] + col

    results = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        val = first.value
        if not (isinstance(val, ast.Constant) and isinstance(val.value, str)):
            continue

        start = to_offset(val.lineno, val.col_offset)
        end = to_offset(val.end_lineno, val.end_col_offset)
        raw = source[start:end]
        indent = re.match(r"[ \t]*", src_lines[val.lineno - 1]).group(0)

        try:
            info = DocstringInfo(
                start,
                end,
                raw,
                indent,
                owner_kind=type(node).__name__,
                owner_name=_owner_name(node),
                owner_lineno=1 if isinstance(node, ast.Module) else node.lineno,
            )
        except ValueError as e:
            where = f"{path_for_warnings}:" if path_for_warnings else ""
            print(f"!! {where}{val.lineno}: skipping docstring ({e})", file=sys.stderr)
            continue

        if not info.is_multiline:
            continue

        results.append(info)

    results.sort(key=lambda i: i.start)
    return results


def collect_files(path, recursive):
    path = Path(path)
    if path.is_file():
        return [path]
    if recursive:
        return sorted(path.rglob("*.py"))
    return sorted(path.glob("*.py"))


def process_file(path, convert_target, dry_run, stats, color=False):
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"!! {path}: could not read file ({e})", file=sys.stderr)
        return

    try:
        infos = find_docstrings(source, path_for_warnings=path)
    except SyntaxError as e:
        print(f"!! {path}: syntax error, skipped ({e})", file=sys.stderr)
        return

    if not infos:
        return

    for info in infos:
        stats[info.style] += 1

    if convert_target is None:
        for info in infos:
            print(
                f"{path}:{info.owner_lineno}: [{info.style:5}] {info.owner_kind} {info.owner_name}"
            )
        return

    new_source = source
    changed = False
    # Apply edits from the end of the file backwards so earlier offsets
    # (computed against the original source) stay valid as we go.
    for info in reversed(infos):
        new_raw = info.converted(convert_target)
        if new_raw != info.raw:
            changed = True
            new_source = new_source[: info.start] + new_raw + new_source[info.end :]

    if not changed:
        return

    if dry_run:
        diff = difflib.unified_diff(
            source.splitlines(keepends=True),
            new_source.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"{path} (converted)",
        )
        if color:
            for line in diff:
                sys.stdout.write(color_diff_line(line))
        else:
            sys.stdout.writelines(diff)
    else:
        path.write_text(new_source, encoding="utf-8")
        print(f"updated {path}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", help="Python file or directory to scan")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories when PATH is a directory",
    )
    parser.add_argument(
        "--convert",
        choices=["below", "same"],
        default=None,
        help="Rewrite all multi-line docstrings to this style "
        "and write the files in place. If omitted, just "
        "reports what styles were found.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --convert, print a unified diff instead of writing files.",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Color the --dry-run diff output (red removed / "
        "green added). Default: auto-detect a terminal.",
    )
    args = parser.parse_args()

    files = collect_files(args.path, args.recursive)
    if not files:
        print("No .py files found.", file=sys.stderr)
        sys.exit(1)

    stats = {"below": 0, "same": 0}
    color = use_color(args.color)
    for f in files:
        process_file(f, args.convert, args.dry_run, stats, color=color)

    if args.convert is None:
        total = stats["below"] + stats["same"]
        print(
            f"\n{total} multi-line docstring(s) found "
            f"({stats['below']} below-style, {stats['same']} same-line style) "
            f"across {len(files)} file(s).",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
