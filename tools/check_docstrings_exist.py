#!/usr/bin/env python3
"""Recursively check a directory of Python files for missing docstrings."""

import argparse
import ast
from pathlib import Path

CATEGORIES = ("module", "class", "function", "method")


def is_private(name: str) -> bool:
    return name.startswith("_")


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def check_file(path: Path, checks: set[str], ignore_private: bool) -> list[str]:
    """Return a list of human-readable issues for one file."""
    issues = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}: could not parse ({e})"]

    if "module" in checks and ast.get_docstring(tree) is None:
        issues.append(f"{path}: module missing docstring")

    def visit(node, in_class):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                if "class" in checks and ast.get_docstring(child) is None:
                    issues.append(
                        f"{path}:{child.lineno}: class '{child.name}' missing docstring"
                    )
                visit(child, in_class=True)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                category = "method" if in_class else "function"
                if category in checks and ast.get_docstring(child) is None:
                    name = child.name
                    skip = (
                        ignore_private
                        and in_class
                        and (is_private(name) or is_dunder(name))
                    )
                    if not skip:
                        issues.append(
                            f"{path}:{child.lineno}: {category} '{name}' missing docstring"
                        )
                visit(child, in_class=False)
            else:
                visit(child, in_class)

    visit(tree, in_class=False)
    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Check a directory tree for missing docstrings."
    )
    parser.add_argument("path", type=Path, help="Directory (or file) to scan")
    parser.add_argument(
        "--check",
        nargs="+",
        choices=CATEGORIES,
        default=list(CATEGORIES),
        help="Which categories to check (default: all)",
    )
    parser.add_argument(
        "--no-ignore-private",
        action="store_true",
        help="Also flag private (_x) and dunder (__x__) methods (default: ignored)",
    )
    args = parser.parse_args()

    checks = set(args.check)
    ignore_private = not args.no_ignore_private

    files = [args.path] if args.path.is_file() else sorted(args.path.rglob("*.py"))

    all_issues = []
    for f in files:
        all_issues.extend(check_file(f, checks, ignore_private))

    for issue in all_issues:
        print(issue)

    print(f"\n{len(all_issues)} issue(s) found across {len(files)} file(s).")


if __name__ == "__main__":
    main()
