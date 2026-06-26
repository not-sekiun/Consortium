#!/usr/bin/env python3
"""
exc_hierarchy_doc.py
=====================

Generate mkdocstrings-compatible exception-hierarchy docstrings from Python
source files, and (optionally) insert/replace them as the module-level
docstring of each target file.

See `--help` (or the bottom of this file) for usage examples.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass
class ExcClass:
    """A single discovered exception class."""

    name: str
    base_names: list[str]  # names of bases as written in source (unresolved)
    module_path: str  # dotted path, e.g. consortium.server.exceptions.foo
    file_path: Path
    lineno: int
    children: list[ExcClass] = field(default_factory=list)

    @property
    def qualified(self) -> str:
        return f"{self.module_path}.{self.name}"


# --------------------------------------------------------------------------- #
# Step 1: discover files
# --------------------------------------------------------------------------- #


def collect_python_files(paths: Sequence[Path], recursive: bool) -> list[Path]:
    """Resolve a mix of file/dir paths into a flat, deduplicated list of .py files."""
    files: list[Path] = []
    seen: set[Path] = set()

    for p in paths:
        if p.is_file():
            if p.suffix == ".py":
                rp = p.resolve()
                if rp not in seen:
                    seen.add(rp)
                    files.append(p)
            else:
                print(f"warning: skipping non-.py file: {p}", file=sys.stderr)
        elif p.is_dir():
            globber = p.rglob("*.py") if recursive else p.glob("*.py")
            for f in sorted(globber):
                rp = f.resolve()
                if rp not in seen:
                    seen.add(rp)
                    files.append(f)
        else:
            print(f"warning: path does not exist: {p}", file=sys.stderr)

    return files


# --------------------------------------------------------------------------- #
# Step 2: figure out each file's dotted module path
# --------------------------------------------------------------------------- #


def infer_module_path(file_path: Path, package_root: Path | None) -> str:
    """
    Build a dotted module path for `file_path`.

    If `package_root` is given, the path is made relative to it.
    Otherwise we walk upward from the file while `__init__.py` files are
    present, treating that walk as the package chain (standard Python
    package-discovery heuristic).
    """
    file_path = file_path.resolve()

    if package_root is not None:
        package_root = package_root.resolve()
        try:
            rel = file_path.relative_to(package_root)
        except ValueError:
            # Not actually under package_root; fall back to filename only.
            rel = Path(file_path.name)
        parts = list(rel.parts)
    else:
        # Walk upward while __init__.py exists in the parent directory,
        # collecting directory names, then prepend.
        parts = [file_path.stem]
        current_dir = file_path.parent
        while (current_dir / "__init__.py").exists():
            parts.insert(0, current_dir.name)
            if current_dir.parent == current_dir:
                break
            current_dir = current_dir.parent

    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    elif parts and parts[-1] == "__init__":
        parts.pop()

    # strip a trailing "__init__" module name (module IS the package)
    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts)


# --------------------------------------------------------------------------- #
# Step 3: parse files for exception class definitions
# --------------------------------------------------------------------------- #


def base_name_from_node(node: ast.expr) -> str | None:
    """Extract a usable name from a base-class expression (Name or Attribute)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr  # use the rightmost component, e.g. mod.Foo -> Foo
    return None


def parse_file_for_classes(file_path: Path, module_path: str) -> list[ExcClass]:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"warning: could not parse {file_path}: {e}", file=sys.stderr)
        return []

    classes: list[ExcClass] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [n for n in (base_name_from_node(b) for b in node.bases) if n]
            classes.append(
                ExcClass(
                    name=node.name,
                    base_names=base_names,
                    module_path=module_path,
                    file_path=file_path,
                    lineno=node.lineno,
                )
            )
    return classes


# --------------------------------------------------------------------------- #
# Step 4: build hierarchy (per "scope" -- see CLI semantics below)
# --------------------------------------------------------------------------- #

LIKELY_EXC_SUFFIXES = ("Error", "Exception")


def looks_like_exception_name(name: str) -> bool:
    return name.endswith(LIKELY_EXC_SUFFIXES)


def build_hierarchy(
    classes: list[ExcClass],
    extra_root_name: str | None = None,
) -> tuple[list[ExcClass], dict[str, ExcClass]]:
    """
    Given all discovered classes (already filtered to one scope: a single
    module or a merged set, depending on caller), wire up parent/child
    relationships using base_names, and return the list of root nodes
    (those whose base isn't itself a discovered class) plus a name->class map.

    Only classes that are part of an exception-like chain are kept:
    a class is included if itself or one of its bases (transitively)
    looks like an exception name, OR if it is directly reachable from
    another included class.
    """
    by_name: dict[str, ExcClass] = {c.name: c for c in classes}

    # Determine which classes are "in scope" as exceptions at all.
    # A class qualifies if its name looks like an exception, or if any of
    # its bases (recursively, within this file-set) looks like one.
    def is_exception_like(c: ExcClass, _seen: set[str] | None = None) -> bool:
        _seen = _seen or set()
        if c.name in _seen:
            return False
        _seen.add(c.name)
        if looks_like_exception_name(c.name):
            return True
        for b in c.base_names:
            if looks_like_exception_name(b):
                return True
            if b in by_name and is_exception_like(by_name[b], _seen):
                return True
        return False

    in_scope = [c for c in classes if is_exception_like(c)]
    in_scope_names = {c.name for c in in_scope}

    roots: list[ExcClass] = []

    for c in in_scope:
        c.children = []  # reset in case of re-use

    for c in in_scope:
        parent = None
        for b in c.base_names:
            if b in by_name and b in in_scope_names:
                parent = by_name[b]
                break
        if parent is not None:
            parent.children.append(c)
        else:
            roots.append(c)

    # Optionally synthesize an out-of-scope root that adopts every existing
    # root as a child, if the user wants e.g. BaseConsortiumError shown even
    # though it isn't defined in the scanned files.
    if extra_root_name:
        synthetic = ExcClass(
            name=extra_root_name,
            base_names=[],
            module_path="__external__",  # caller fills in real path
            file_path=Path(),
            lineno=0,
            children=list(roots),
        )
        roots = [synthetic]

    return roots, by_name


# --------------------------------------------------------------------------- #
# Step 5: sorting
# --------------------------------------------------------------------------- #


def sort_hierarchy(roots: list[ExcClass]) -> None:
    """Recursively sort siblings alphabetically, in place."""
    roots.sort(key=lambda c: c.name)
    for c in roots:
        sort_hierarchy(c.children)


# --------------------------------------------------------------------------- #
# Step 6: render docstring
# --------------------------------------------------------------------------- #


def render_node(c: ExcClass, depth: int, lines: list[str]) -> None:
    indent = "    " * depth
    if c.module_path == "__external__":
        # synthetic out-of-scope root: render name only, no mkdocstrings link,
        # since we don't actually know its real location.
        lines.append(f"{indent}- `{c.name}`")
    else:
        link_target = f"{c.module_path}.{c.name}"
        lines.append(f"{indent}- [`{c.name}`][{link_target}]")
    for child in c.children:
        render_node(child, depth + 1, lines)


def render_docstring(
    roots: list[ExcClass],
    heading: str,
    extra_root_module_path: str | None = None,
) -> str:
    if extra_root_module_path and roots and roots[0].module_path == "__external__":
        roots[0].module_path = extra_root_module_path

    lines: list[str] = ['"""', heading, ""]
    for r in roots:
        render_node(r, 0, lines)
    lines.append('"""')
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Step 7: file insertion / replacement
# --------------------------------------------------------------------------- #


def get_existing_module_docstring_span(source: str) -> tuple[int, int] | None:
    """
    Return (start_char, end_char) of the existing module docstring in `source`,
    if one exists as the very first statement, else None.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    if not tree.body:
        return None
    first = tree.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return (
            first.value.col_offset,
            first.value.end_col_offset,
            first.lineno,
            first.value.end_lineno,
        )  # type: ignore
    return None


def existing_docstring_text(file_path: Path) -> str | None:
    source = file_path.read_text(encoding="utf-8")
    span = get_existing_module_docstring_span(source)
    if span is None:
        return None
    lines = source.splitlines(keepends=True)
    start_line, end_line = span[2], span[3]
    return "".join(lines[start_line - 1 : end_line])


def insert_or_replace_docstring(
    file_path: Path,
    new_docstring: str,
    replace: bool,
    auto_confirm: bool,
) -> bool:
    """
    Insert `new_docstring` at the top of file_path. If a module docstring
    already exists:
      - if replace=True: swap it out for the new one (after confirmation).
      - if replace=False: insert the new one above it (after confirmation),
        leaving the old one intact, separated by a blank line.
    Returns True if the file was modified.
    """
    source = file_path.read_text(encoding="utf-8")
    span = get_existing_module_docstring_span(source)
    lines = source.splitlines(keepends=True)

    print(f"\n--- {file_path} ---")
    if span is not None:
        start_line, end_line = span[2], span[3]
        current = "".join(lines[start_line - 1 : end_line])
        print("Current top-of-file docstring:")
        print(current)
    else:
        print("(No existing module docstring found.)")

    if not auto_confirm:
        verb = "replace" if (replace and span is not None) else "insert"
        resp = (
            input(f"Proceed to {verb} docstring in this file? [y/N]: ").strip().lower()
        )
        if resp not in ("y", "yes"):
            print("Skipped.")
            return False

    if span is not None and replace:
        start_line, end_line = span[2], span[3]
        new_lines = lines[: start_line - 1] + [new_docstring + "\n"] + lines[end_line:]
    elif span is not None and not replace:
        start_line, _ = span[2], span[3]
        new_lines = (
            lines[: start_line - 1] + [new_docstring + "\n\n"] + lines[start_line - 1 :]
        )
    else:
        new_lines = [new_docstring + "\n\n"] + lines

    file_path.write_text("".join(new_lines), encoding="utf-8")
    print("Updated.")
    return True


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def process_per_file(
    files: list[Path],
    package_root: Path | None,
    sort_alpha: bool,
    extra_root_name: str | None,
    extra_root_module_path: str | None,
    heading_template: str,
) -> dict[Path, str]:
    """Build one docstring per input file, scoped to that file's own classes."""
    results: dict[Path, str] = {}
    for f in files:
        mod_path = infer_module_path(f, package_root)
        classes = parse_file_for_classes(f, mod_path)
        roots, _ = build_hierarchy(classes, extra_root_name=extra_root_name)
        if not roots:
            continue
        if sort_alpha:
            sort_hierarchy(roots)
        heading = heading_template.format(filename=f.stem, module=mod_path)
        doc = render_docstring(roots, heading, extra_root_module_path)
        results[f] = doc
    return results


def process_merged(
    files: list[Path],
    package_root: Path | None,
    sort_alpha: bool,
    extra_root_name: str | None,
    extra_root_module_path: str | None,
    heading: str,
) -> str | None:
    """Build a single merged docstring across all classes found in all files."""
    all_classes: list[ExcClass] = []
    for f in files:
        mod_path = infer_module_path(f, package_root)
        all_classes.extend(parse_file_for_classes(f, mod_path))

    roots, _ = build_hierarchy(all_classes, extra_root_name=extra_root_name)
    if not roots:
        return None
    if sort_alpha:
        sort_hierarchy(roots)
    return render_docstring(roots, heading, extra_root_module_path)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

EPILOGUE = """\
examples:

  # Display the generated hierarchy docstring for a single file (no file changes)
  python exc_hierarchy_doc.py path/to/listeners_consortium_exceptions.py

  # Display, recursively scanning an entire directory, one docstring per module
  python exc_hierarchy_doc.py --recursive src/consortium/server/exceptions/

  # Merge every exception across a directory into ONE combined hierarchy docstring
  python exc_hierarchy_doc.py --recursive --merge src/consortium/server/exceptions/

  # Same as above, but sort siblings alphabetically at every level
  python exc_hierarchy_doc.py --recursive --sort src/consortium/server/exceptions/

  # Insert the docstring at the top of each file (prompts per file, shows
  # current top-of-file content first; does NOT remove any existing docstring)
  python exc_hierarchy_doc.py --recursive --insert src/consortium/server/exceptions/

  # Same, but REPLACE any existing top-of-file docstring instead of inserting above it
  python exc_hierarchy_doc.py --recursive --insert --replace src/consortium/server/exceptions/

  # Skip the confirmation prompt when inserting/replacing (use with care)
  python exc_hierarchy_doc.py --recursive --insert --replace --yes src/consortium/server/exceptions/

  # Include an out-of-scope base exception as the synthetic root of the hierarchy,
  # pointing it at a real importable location for the mkdocstrings link
  python exc_hierarchy_doc.py path/to/listeners_consortium_exceptions.py \\
      --extra-root BaseConsortiumError \\
      --extra-root-path consortium.server.exceptions.base_consortium_exception

  # Explicitly set the package root used to compute dotted module paths
  # (otherwise inferred by walking up through __init__.py files)
  python exc_hierarchy_doc.py --recursive --package-root src/ src/consortium/server/exceptions/
"""


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate mkdocstrings-style exception-hierarchy docstrings from "
            "Python source files containing exception class definitions."
        ),
        epilog=EPILOGUE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="One or more files and/or directories to scan.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="When a directory is given, scan it recursively. "
        "Without this flag, only top-level *.py files in each directory are scanned.",
    )
    parser.add_argument(
        "-m",
        "--merge",
        action="store_true",
        help="Merge all discovered exception classes (across all input files) into a "
        "single combined hierarchy docstring, instead of one docstring per file.",
    )
    parser.add_argument(
        "-s",
        "--sort",
        action="store_true",
        help="Sort sibling exceptions alphabetically at every level of the hierarchy. "
        "Default: preserve source encounter order (still grouped by parent).",
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=None,
        help="Root directory used to compute dotted module paths "
        "(e.g. 'src/'). If omitted, module paths are inferred by walking "
        "upward through directories containing __init__.py.",
    )
    parser.add_argument(
        "--extra-root",
        dest="extra_root_name",
        default=None,
        metavar="NAME",
        help="Name of an out-of-scope base exception (not defined in the scanned "
        "files) to insert as the synthetic root of the generated hierarchy, "
        "e.g. BaseConsortiumError.",
    )
    parser.add_argument(
        "--extra-root-path",
        dest="extra_root_module_path",
        default=None,
        metavar="DOTTED.MODULE.PATH",
        help="Dotted module path for --extra-root, used to build its mkdocstrings "
        "link target, e.g. consortium.server.exceptions.base_consortium_exception. "
        "If omitted, the extra root is rendered as plain `Name` with no link.",
    )
    parser.add_argument(
        "--heading",
        default="Exception hierarchy for {filename} errors:",
        help="Heading line placed at the top of each generated docstring "
        "(before the hierarchy list). Supports {filename} and {module} "
        "placeholders. Default: %(default)r. Ignored (a generic heading is "
        "used) when --merge is set unless --merge-heading is also given.",
    )
    parser.add_argument(
        "--merge-heading",
        default="Exception hierarchy:",
        help="Heading line used for the single docstring produced by --merge. "
        "Default: %(default)r.",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-i",
        "--insert",
        action="store_true",
        help="Instead of just printing the generated docstring(s), insert each one "
        "at the top of its corresponding file. Shows the current top-of-file "
        "content and prompts for confirmation per file unless --yes is given. "
        "By default this inserts ABOVE any existing module docstring rather "
        "than removing it; combine with --replace to overwrite instead.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Only meaningful with --insert: replace an existing top-of-file "
        "module docstring instead of inserting above it.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Only meaningful with --insert: skip the confirmation prompt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.merge and args.insert:
        parser.error(
            "--merge and --insert cannot be combined (a merged hierarchy "
            "has no single file to insert into). Run merge mode without "
            "--insert to view/save it separately."
        )

    files = collect_python_files(args.paths, recursive=args.recursive)
    if not files:
        print("No Python files found to scan.", file=sys.stderr)
        return 1

    if args.merge:
        doc = process_merged(
            files=files,
            package_root=args.package_root,
            sort_alpha=args.sort,
            extra_root_name=args.extra_root_name,
            extra_root_module_path=args.extra_root_module_path,
            heading=args.merge_heading,
        )
        if doc is None:
            print("No exception classes found across the given files.", file=sys.stderr)
            return 1
        print(doc)
        return 0

    results = process_per_file(
        files=files,
        package_root=args.package_root,
        sort_alpha=args.sort,
        extra_root_name=args.extra_root_name,
        extra_root_module_path=args.extra_root_module_path,
        heading_template=args.heading,
    )

    if not results:
        print("No exception classes found in any of the given files.", file=sys.stderr)
        return 1

    if not args.insert:
        for f, doc in results.items():
            print(f"\n# {f}")
            print(doc)
        return 0

    any_changed = False
    for f, doc in results.items():
        changed = insert_or_replace_docstring(
            file_path=f,
            new_docstring=doc,
            replace=args.replace,
            auto_confirm=args.yes,
        )
        any_changed = any_changed or changed

    return 0 if any_changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
