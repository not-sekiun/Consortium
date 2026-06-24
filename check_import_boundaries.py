#!/usr/bin/env python3
"""
check_import_boundaries.py

Enforces a one-way import boundary between two packages that live in the
same repo but are conceptually separate (e.g. `framework` and `server`).

Rule:
    `framework` must never import from `server`,
    except for a small, explicitly allow-listed set of (file, imported_module)
    pairs that represent deliberate, documented exceptions.

`server` importing from `framework` is always fine and is not checked.

Usage:
    python check_import_boundaries.py \
        --restricted-dir framework \
        --forbidden-package server \
        --allow framework/base_plugin.py:server.services.namespace

    # or configure everything in a config file (see CONFIG below) and just run:
    python check_import_boundaries.py

Exit code is 0 if clean, 1 if violations were found (suitable for CI).
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import pathlib
import sys

# ---------------------------------------------------------------------------
# Config: edit these defaults to match your repo, or override via CLI flags.
# ---------------------------------------------------------------------------

DEFAULT_RESTRICTED_DIR = "framework"
DEFAULT_FORBIDDEN_PACKAGE = "server"

# Format: "relative/path/to/file.py:dotted.module.prefix"
# A violation is allowed if the importing file's relative path matches the
# left side AND the imported module starts with the dotted prefix on the
# right side. This lets you scope the exception tightly (a specific file
# importing a specific module), rather than allow-listing an entire file
# for everything, or an entire module for every importer.
DEFAULT_ALLOWLIST: tuple[str, ...] = ("base_plugin.py:server.services.namespace",)


@dataclasses.dataclass(frozen=True)
class Violation:
    file: pathlib.Path
    lineno: int
    imported_module: str
    is_allowlisted: bool


@dataclasses.dataclass(frozen=True)
class AllowRule:
    file_suffix: str  # matched via str endswith against the relative path
    module_prefix: str

    def matches(self, relative_path: pathlib.Path, imported_module: str) -> bool:
        return str(relative_path).endswith(self.file_suffix) and (
            imported_module == self.module_prefix
            or imported_module.startswith(self.module_prefix + ".")
        )


def parse_allowlist(raw_rules: list[str]) -> list[AllowRule]:
    rules = []
    for raw in raw_rules:
        if ":" not in raw:
            raise ValueError(
                f"Malformed --allow entry '{raw}'. Expected 'path/suffix.py:module.prefix'."
            )
        file_suffix, module_prefix = raw.split(":", 1)
        rules.append(AllowRule(file_suffix=file_suffix, module_prefix=module_prefix))
    return rules


def iter_python_files(root: pathlib.Path):
    yield from root.rglob("*.py")


def extract_imported_modules(tree: ast.Module) -> list[tuple[int, str]]:
    """
    Returns a list of (lineno, dotted_module_name) for every import statement
    in the file. Handles both `import x.y.z` and `from x.y import z`.
    For `from . import z` / relative imports, level > 0 and module may be
    None or partial -- those can never refer to an external top-level
    package by definition, so they are skipped (they're intra-package
    relative imports, not cross-package ones).
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # relative import (e.g. "from . import x" / "from .. import y")
                # cannot reference an external top-level package
                continue
            if node.module:
                found.append((node.lineno, node.module))
    return found


def module_touches_forbidden_package(module_name: str, forbidden_package: str) -> bool:
    return module_name == forbidden_package or module_name.startswith(
        forbidden_package + "."
    )


def check_file(
    filepath: pathlib.Path,
    repo_root: pathlib.Path,
    forbidden_package: str,
    allow_rules: list[AllowRule],
) -> list[Violation]:
    try:
        source = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        print(f"WARNING: could not read {filepath}: {exc}", file=sys.stderr)
        return []

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        print(f"WARNING: could not parse {filepath}: {exc}", file=sys.stderr)
        return []

    relative_path = filepath.relative_to(repo_root)
    violations: list[Violation] = []

    for lineno, module_name in extract_imported_modules(tree):
        if not module_touches_forbidden_package(module_name, forbidden_package):
            continue

        is_allowlisted = any(
            rule.matches(relative_path, module_name) for rule in allow_rules
        )
        violations.append(
            Violation(
                file=relative_path,
                lineno=lineno,
                imported_module=module_name,
                is_allowlisted=is_allowlisted,
            )
        )

    return violations


def run_check(
    restricted_dir: pathlib.Path,
    repo_root: pathlib.Path,
    forbidden_package: str,
    allow_rules: list[AllowRule],
) -> tuple[list[Violation], list[Violation]]:
    """
    Returns (hard_violations, allowlisted_violations).
    """
    all_violations: list[Violation] = []
    for filepath in iter_python_files(restricted_dir):
        all_violations.extend(
            check_file(filepath, repo_root, forbidden_package, allow_rules)
        )

    hard = [v for v in all_violations if not v.is_allowlisted]
    allowlisted = [v for v in all_violations if v.is_allowlisted]
    return hard, allowlisted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="Repo root, used to compute relative paths and resolve --restricted-dir. Default: cwd.",
    )
    parser.add_argument(
        "--restricted-dir",
        default=DEFAULT_RESTRICTED_DIR,
        help=f"Directory to scan (relative to --repo-root). Default: {DEFAULT_RESTRICTED_DIR!r}.",
    )
    parser.add_argument(
        "--forbidden-package",
        default=DEFAULT_FORBIDDEN_PACKAGE,
        help=f"Top-level package the restricted dir must not import. Default: {DEFAULT_FORBIDDEN_PACKAGE!r}.",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help=(
            "Allow-list entry as 'path_suffix.py:module.prefix'. "
            "Can be passed multiple times. Combined with built-in defaults "
            "unless --no-default-allowlist is set."
        ),
    )
    parser.add_argument(
        "--no-default-allowlist",
        action="store_true",
        help="Ignore the built-in DEFAULT_ALLOWLIST and only use --allow entries.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print violations, suppress the clean-pass summary line.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    restricted_dir = (repo_root / args.restricted_dir).resolve()

    if not restricted_dir.is_dir():
        print(
            f"ERROR: restricted dir '{restricted_dir}' does not exist or is not a directory.",
            file=sys.stderr,
        )
        return 2

    raw_allow_entries = list(args.allow)
    if not args.no_default_allowlist:
        raw_allow_entries = list(DEFAULT_ALLOWLIST) + raw_allow_entries

    try:
        allow_rules = parse_allowlist(raw_allow_entries)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    hard_violations, allowlisted_violations = run_check(
        restricted_dir=restricted_dir,
        repo_root=repo_root,
        forbidden_package=args.forbidden_package,
        allow_rules=allow_rules,
    )

    if allowlisted_violations and not args.quiet:
        print("Allow-listed crossings (informational, not failing the build):")
        for v in sorted(allowlisted_violations, key=lambda v: (str(v.file), v.lineno)):
            print(f"  {v.file}:{v.lineno}  imports '{v.imported_module}'")
        print()

    if hard_violations:
        print(
            f"FOUND {len(hard_violations)} import-direction violation(s): "
            f"'{args.restricted_dir}' must not import '{args.forbidden_package}'.\n",
            file=sys.stderr,
        )
        for v in sorted(hard_violations, key=lambda v: (str(v.file), v.lineno)):
            print(
                f"  {v.file}:{v.lineno}  imports '{v.imported_module}'",
                file=sys.stderr,
            )
        print(
            "\nIf this crossing is intentional, add it to the allowlist "
            "(DEFAULT_ALLOWLIST in this script, or via --allow) with a comment "
            "explaining why, and add a matching NOTE comment at the import site itself.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"OK: no unsanctioned imports of '{args.forbidden_package}' found under "
            f"'{args.restricted_dir}'."
            + (
                f" ({len(allowlisted_violations)} allow-listed crossing(s).)"
                if allowlisted_violations
                else ""
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
