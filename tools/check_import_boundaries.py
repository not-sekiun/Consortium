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

WHY THIS VERSION IS DIFFERENT FROM A PLAIN IMPORT-DIRECTION LINTER
-------------------------------------------------------------------
A flat "framework imports server -> fail" check treats every crossing as
equally bad. In practice (and very much in this repo's case) most crossings
fall into one of three buckets, in increasing order of how much they should
worry you if `framework` is ever split into its own standalone package:

  1. TYPE_CHECKING-guarded   - the import only happens inside
     `if TYPE_CHECKING:`. It never executes at runtime. Zero coupling risk
     today; only matters for static type checkers / IDEs, and is trivially
     solvable later with a Protocol, a stub, or a string forward-ref.

  2. annotation-only         - the import is a normal, unguarded import,
     so it *does* execute at module load time, but every use of the
     imported name in this file is inside a type annotation (function
     signature, return type, `: Foo` variable annotation). This is a real
     but *easily removable* runtime dependency: wrap it in
     `if TYPE_CHECKING:` and the crossing disappears.

  3. structural              - the imported name is used in actual runtime
     logic: a call, instantiation, base class, decorator, isinstance/
     issubclass check, exception handler, attribute access outside an
     annotation, etc. This is genuine coupling and is the kind of thing
     that will actually block splitting `framework` out as a standalone
     package.

There's also a 4th, informational bucket:

  4. unused-or-string-only   - we found no Name reference to the imported
     binding anywhere else in the file. Either it's dead code, or it's only
     referenced inside a string forward-reference annotation we didn't
     parse (e.g. `def f(x: "server.Foo")` without `from __future__ import
     annotations`). Worth a human glance, but not a structural risk.

Usage:
    python check_import_boundaries.py \
        --restricted-dir framework \
        --forbidden-package server \
        --allow framework/base_plugin.py:server.services.namespace

    # or configure everything in a config file (see CONFIG below) and just run:
    python check_import_boundaries.py

Exit code is 0 if clean (per --fail-on), 1 if violations were found that
meet the failure threshold (suitable for CI), 2 on a usage/config error.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import enum
import pathlib
import re
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


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------


class Severity(enum.Enum):
    TYPE_CHECKING_GUARDED = "type_checking_guarded"
    ANNOTATION_ONLY = "annotation_only"
    UNUSED_OR_STRING_ONLY = "unused_or_string_only"
    STRUCTURAL = "structural"

    @property
    def rank(self) -> int:
        # Higher rank == more pressing. Used for sorting and --fail-on.
        return {
            Severity.TYPE_CHECKING_GUARDED: 0,
            Severity.UNUSED_OR_STRING_ONLY: 1,
            Severity.ANNOTATION_ONLY: 2,
            Severity.STRUCTURAL: 3,
        }[self]

    @property
    def label(self) -> str:
        return {
            Severity.TYPE_CHECKING_GUARDED: "TYPE_CHECKING-guarded",
            Severity.ANNOTATION_ONLY: "annotation-only",
            Severity.UNUSED_OR_STRING_ONLY: "unused/string-only",
            Severity.STRUCTURAL: "structural",
        }[self]

    # ANSI fallback colors (used when `rich` isn't installed).
    @property
    def ansi(self) -> str:
        return {
            Severity.TYPE_CHECKING_GUARDED: "\033[2;32m",  # dim green
            Severity.ANNOTATION_ONLY: "\033[33m",  # yellow
            Severity.UNUSED_OR_STRING_ONLY: "\033[2;34m",  # dim blue
            Severity.STRUCTURAL: "\033[1;31m",  # bold red
        }[self]

    # rich markup tag equivalents.
    @property
    def rich_style(self) -> str:
        return {
            Severity.TYPE_CHECKING_GUARDED: "dim green",
            Severity.ANNOTATION_ONLY: "yellow",
            Severity.UNUSED_OR_STRING_ONLY: "dim blue",
            Severity.STRUCTURAL: "bold red",
        }[self]


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"


@dataclasses.dataclass(frozen=True)
class Violation:
    file: pathlib.Path
    lineno: int
    imported_module: str  # full dotted path, e.g. "server.utils.helpers.Foo"
    bound_name: str  # the local name this import binds, used for usage analysis
    severity: Severity
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


# ---------------------------------------------------------------------------
# Import extraction
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ImportRef:
    lineno: int
    imported_module: str  # full dotted path for reporting
    bound_name: str  # local name introduced into the namespace
    node_id: int  # id() of the AST import node, to exclude it from usage scans


def extract_imports(tree: ast.Module) -> list[ImportRef]:
    """
    Returns one ImportRef per *bound name*, not per import statement, so
    `from server.x import Foo, Bar` yields two independent entries (Foo may
    be used structurally while Bar is annotation-only, and we want that
    distinction).

    For `from . import x` / relative imports, level > 0 and module may be
    None or partial -- those can never refer to an external top-level
    package by definition, so they are skipped (they're intra-package
    relative imports, not cross-package ones).
    """
    found: list[ImportRef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # `import a.b.c` binds only the top-level name `a` (unless
                # aliased, in which case it binds the full thing to asname).
                bound_name = alias.asname or alias.name.split(".")[0]
                found.append(
                    ImportRef(
                        lineno=node.lineno,
                        imported_module=alias.name,
                        bound_name=bound_name,
                        node_id=id(node),
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if not node.module:
                continue
            for alias in node.names:
                if alias.name == "*":
                    # star-import: we can't know the bound names; report the
                    # module itself with a synthetic bound name that will
                    # never match anything, so it falls through to
                    # "unused_or_string_only" (flag for human review).
                    found.append(
                        ImportRef(
                            lineno=node.lineno,
                            imported_module=f"{node.module}.*",
                            bound_name="*",
                            node_id=id(node),
                        )
                    )
                    continue
                bound_name = alias.asname or alias.name
                found.append(
                    ImportRef(
                        lineno=node.lineno,
                        imported_module=f"{node.module}.{alias.name}",
                        bound_name=bound_name,
                        node_id=id(node),
                    )
                )
    return found


def module_touches_forbidden_package(module_name: str, forbidden_package: str) -> bool:
    return module_name == forbidden_package or module_name.startswith(
        forbidden_package + "."
    )


# ---------------------------------------------------------------------------
# Severity classification helpers
# ---------------------------------------------------------------------------


def _is_type_checking_test(test: ast.expr) -> bool:
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    return False


def _collect_type_checking_guarded_ids(tree: ast.Module) -> set[int]:
    """Node ids of every statement/expression that only runs under
    `if TYPE_CHECKING:` and therefore never executes at runtime."""
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_type_checking_test(node.test):
            for stmt in node.body:
                guarded.add(id(stmt))
                for sub in ast.walk(stmt):
                    guarded.add(id(sub))
    return guarded


def _collect_annotation_ids(tree: ast.Module) -> set[int]:
    """Node ids of every AST node that lives strictly inside a type
    annotation (function arg/return annotations, AnnAssign annotations)."""
    annotation_ids: set[int] = set()

    def _mark(expr: ast.expr | None) -> None:
        if expr is None:
            return
        for sub in ast.walk(expr):
            annotation_ids.add(id(sub))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            for a in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                _mark(a.annotation)
            if args.vararg:
                _mark(args.vararg.annotation)
            if args.kwarg:
                _mark(args.kwarg.annotation)
            _mark(node.returns)
        elif isinstance(node, ast.AnnAssign):
            _mark(node.annotation)
    return annotation_ids


_STRING_FORWARD_REF_RE_CACHE: dict[str, re.Pattern] = {}


def _bound_name_appears_in_string_annotations(
    tree: ast.Module, bound_name: str
) -> bool:
    """Best-effort detection of forward-ref usage inside string annotations,
    e.g. def f(x: "server.Foo"), which plain Name-node matching can't see."""
    pattern = _STRING_FORWARD_REF_RE_CACHE.get(bound_name)
    if pattern is None:
        pattern = re.compile(r"\b" + re.escape(bound_name) + r"\b")
        _STRING_FORWARD_REF_RE_CACHE[bound_name] = pattern

    def _check(expr: ast.expr | None) -> bool:
        return bool(
            expr is not None
            and isinstance(expr, ast.Constant)
            and isinstance(expr.value, str)
            and pattern.search(expr.value)
        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            for a in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                if _check(a.annotation):
                    return True
            if args.vararg and _check(args.vararg.annotation):
                return True
            if args.kwarg and _check(args.kwarg.annotation):
                return True
            if _check(node.returns):
                return True
        elif isinstance(node, ast.AnnAssign):
            if _check(node.annotation):
                return True
    return False


def classify_severity(
    tree: ast.Module,
    import_ref: ImportRef,
    type_checking_guarded_ids: set[int],
    annotation_ids: set[int],
) -> Severity:
    if import_ref.node_id in type_checking_guarded_ids:
        return Severity.TYPE_CHECKING_GUARDED

    if import_ref.bound_name == "*":
        # star-import: can't trace usage of individual names.
        return Severity.UNUSED_OR_STRING_ONLY

    saw_any_usage = False
    saw_non_annotation_usage = False

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id == import_ref.bound_name
            and isinstance(node.ctx, ast.Load)
        ):
            saw_any_usage = True
            if id(node) not in annotation_ids:
                saw_non_annotation_usage = True
                break  # already as bad as it gets; no need to keep scanning

    if saw_non_annotation_usage:
        return Severity.STRUCTURAL
    if saw_any_usage:
        return Severity.ANNOTATION_ONLY
    if _bound_name_appears_in_string_annotations(tree, import_ref.bound_name):
        return Severity.ANNOTATION_ONLY
    return Severity.UNUSED_OR_STRING_ONLY


# ---------------------------------------------------------------------------
# Per-file / repo-wide checking
# ---------------------------------------------------------------------------


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

    forbidden_imports = [
        ref
        for ref in extract_imports(tree)
        if module_touches_forbidden_package(ref.imported_module, forbidden_package)
    ]
    if not forbidden_imports:
        return []

    type_checking_guarded_ids = _collect_type_checking_guarded_ids(tree)
    annotation_ids = _collect_annotation_ids(tree)

    violations: list[Violation] = []
    for ref in forbidden_imports:
        severity = classify_severity(
            tree, ref, type_checking_guarded_ids, annotation_ids
        )
        is_allowlisted = any(
            rule.matches(relative_path, ref.imported_module) for rule in allow_rules
        )
        violations.append(
            Violation(
                file=relative_path,
                lineno=ref.lineno,
                imported_module=ref.imported_module,
                bound_name=ref.bound_name,
                severity=severity,
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
    """Returns (hard_violations, allowlisted_violations)."""
    all_violations: list[Violation] = []
    for filepath in iter_python_files(restricted_dir):
        all_violations.extend(
            check_file(filepath, repo_root, forbidden_package, allow_rules)
        )

    hard = [v for v in all_violations if not v.is_allowlisted]
    allowlisted = [v for v in all_violations if v.is_allowlisted]
    return hard, allowlisted


# ---------------------------------------------------------------------------
# Reporting: rich if available, ANSI fallback otherwise.
# ---------------------------------------------------------------------------


def _sort_key(v: Violation):
    # Most pressing first within each section.
    return (-v.severity.rank, str(v.file), v.lineno)


def _try_rich_report(
    hard: list[Violation],
    allowlisted: list[Violation],
    restricted_dir: str,
    forbidden_package: str,
    quiet: bool,
) -> bool:
    """Returns True if it successfully rendered with rich, False if rich
    isn't installed (caller should fall back to plain ANSI)."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
    except ImportError:
        return False

    console = Console()

    def render_table(
        title: str, violations: list[Violation], border_style: str
    ) -> None:
        table = Table(title=title, border_style=border_style, header_style="bold")
        table.add_column("File")
        table.add_column("Line", justify="right")
        table.add_column("Imports")
        table.add_column("Severity")
        for v in sorted(violations, key=_sort_key):
            table.add_row(
                str(v.file),
                str(v.lineno),
                v.imported_module,
                Text(v.severity.label, style=v.severity.rich_style),
            )
        console.print(table)

    if allowlisted and not quiet:
        render_table(
            "Allow-listed crossings (informational, not failing the build)",
            allowlisted,
            "blue",
        )

    if hard:
        console.print(
            f"\n[bold red]FOUND {len(hard)} import-direction violation(s):[/] "
            f"'{restricted_dir}' must not import '{forbidden_package}'.\n"
        )
        render_table("Violations", hard, "red")
        console.print(
            "\n[dim]If a crossing is intentional, add it to the allowlist "
            "(DEFAULT_ALLOWLIST in this script, or via --allow) with a comment "
            "explaining why, and add a matching NOTE comment at the import "
            "site itself.[/]"
        )
    elif not quiet:
        suffix = (
            f" ({len(allowlisted)} allow-listed crossing(s).)" if allowlisted else ""
        )
        console.print(
            f"[bold green]OK[/]: no unsanctioned imports of "
            f"'{forbidden_package}' found under '{restricted_dir}'.{suffix}"
        )
    return True


def _ansi_report(
    hard: list[Violation],
    allowlisted: list[Violation],
    restricted_dir: str,
    forbidden_package: str,
    quiet: bool,
) -> None:
    def render_list(title: str, violations: list[Violation], stream) -> None:
        print(f"{ANSI_BOLD}{title}{ANSI_RESET}", file=stream)
        for v in sorted(violations, key=_sort_key):
            color = v.severity.ansi
            print(
                f"  {v.file}:{v.lineno}  imports {ANSI_BOLD}'{v.imported_module}'"
                f"{ANSI_RESET}  [{color}{v.severity.label}{ANSI_RESET}]",
                file=stream,
            )
        print(file=stream)

    if allowlisted and not quiet:
        render_list(
            "Allow-listed crossings (informational, not failing the build):",
            allowlisted,
            sys.stdout,
        )

    if hard:
        print(
            f"{ANSI_BOLD}\033[31mFOUND {len(hard)} import-direction "
            f"violation(s):{ANSI_RESET} '{restricted_dir}' must not import "
            f"'{forbidden_package}'.\n",
            file=sys.stderr,
        )
        render_list("Violations:", hard, sys.stderr)
        print(
            f"{ANSI_DIM}If a crossing is intentional, add it to the allowlist "
            "(DEFAULT_ALLOWLIST in this script, or via --allow) with a comment "
            "explaining why, and add a matching NOTE comment at the import "
            f"site itself.{ANSI_RESET}",
            file=sys.stderr,
        )
    elif not quiet:
        suffix = (
            f" ({len(allowlisted)} allow-listed crossing(s).)" if allowlisted else ""
        )
        print(
            f"\033[1;32mOK{ANSI_RESET}: no unsanctioned imports of "
            f"'{forbidden_package}' found under '{restricted_dir}'.{suffix}"
        )


def report(
    hard: list[Violation],
    allowlisted: list[Violation],
    restricted_dir: str,
    forbidden_package: str,
    quiet: bool,
    no_rich: bool,
) -> None:
    if no_rich or not _try_rich_report(
        hard, allowlisted, restricted_dir, forbidden_package, quiet
    ):
        _ansi_report(hard, allowlisted, restricted_dir, forbidden_package, quiet)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

EPILOG = """\
examples:

  # Use all defaults (framework/ must not import server/), run from repo root
  python check_import_boundaries.py

  # Custom package names
  python check_import_boundaries.py \\
      --restricted-dir consortium/framework \\
      --forbidden-package consortium.server

  # Add a one-off allowed crossing on top of the built-in defaults
  python check_import_boundaries.py \\
      --allow consortium/framework/plugins/base.py:consortium.server.types

  # Ignore the built-in DEFAULT_ALLOWLIST entirely and only use --allow
  python check_import_boundaries.py --no-default-allowlist \\
      --allow consortium/framework/plugins/base.py:consortium.server.types

  # Only fail CI on genuine structural coupling; let TYPE_CHECKING-guarded
  # and annotation-only crossings through as warnings (still printed)
  python check_import_boundaries.py --fail-on structural

  # Fail on anything that isn't purely a TYPE_CHECKING guard, i.e. treat
  # annotation-only (unguarded) imports as build-breaking too
  python check_import_boundaries.py --fail-on annotation_only

  # Run from a different working directory
  python check_import_boundaries.py --repo-root /path/to/consortium

  # Force plain ANSI output even if `rich` is installed
  python check_import_boundaries.py --no-rich

exit codes:
  0  clean (no violations at/above --fail-on threshold)
  1  violations found at/above --fail-on threshold
  2  usage or configuration error (bad --allow entry, missing dir, etc.)
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
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
        "--fail-on",
        choices=["structural", "annotation_only", "type_checking_guarded"],
        default="structural",
        help=(
            "Minimum severity that causes a non-zero exit code (CI gate). "
            "Lower-severity violations are still printed, just not fatal. "
            "Default: 'structural' (only genuine runtime coupling fails the build)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print violations, suppress the clean-pass summary line.",
    )
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Force plain ANSI output even if the 'rich' package is installed.",
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

    report(
        hard=hard_violations,
        allowlisted=allowlisted_violations,
        restricted_dir=args.restricted_dir,
        forbidden_package=args.forbidden_package,
        quiet=args.quiet,
        no_rich=args.no_rich,
    )

    fail_threshold = Severity(args.fail_on).rank
    fatal = [v for v in hard_violations if v.severity.rank >= fail_threshold]
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
