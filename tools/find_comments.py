#!/usr/bin/env python3
"""
find_dead_code.py — Recursively scan a directory for Python files containing
commented-out code (as opposed to ordinary natural-language comments), and
display each finding with file path, line number, and surrounding context,
nicely rendered with `rich`.

Usage:
    python find_dead_code.py [DIRECTORY] [--context N] [--ext .py] [--group] [--theme THEME]

Example:
    python find_dead_code.py ./my_project --context 4 --group
"""

import argparse
import ast
import keyword
import re
import sys
import tokenize
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# --------------------------------------------------------------------------
# ANSI-native theme
#
# Using color names like "red", "green", "yellow", "magenta", "cyan", "blue"
# (rather than hex/RGB) tells rich to emit standard ANSI SGR codes, which
# means the look inherits whatever palette the user's terminal/colorscheme
# defines, instead of rich forcing its own RGB values over top of it.
# "bright_*" variants map to the ANSI bright series (90-97 / 100-107).
# --------------------------------------------------------------------------
ANSI_THEME = Theme(
    {
        "scan.title": "bold cyan",
        "scan.path": "bold blue",
        "scan.lineno": "bold yellow",
        "scan.dim": "dim",
        "scan.ok": "bold green",
        "scan.bad": "bold red",
        "scan.accent": "bold magenta",
        "scan.header.bg": "bold white on blue",
    }
)

console = Console(theme=ANSI_THEME, color_system="standard")


# --------------------------------------------------------------------------
# Detection heuristics
# --------------------------------------------------------------------------

# Tokens that strongly suggest "this is code", used as a secondary signal
# alongside ast.parse() succeeding, to cut down on false positives like
# comments that happen to parse as a single bare identifier or string.
CODE_KEYWORDS = set(keyword.kwlist) - {"True", "False", "None"}

# Patterns commonly found in commented-out code but rare in prose comments.
CODE_PATTERN = re.compile(
    r"""
    ^(?:
        [\w\.\[\]'"]+\s*=\s*[^=]          |   # assignment: x = ..., self.x = ...
        [\w\.]+\(.*\)\s*$                 |   # function/method call: foo(...)
        (import|from)\s+\w+               |   # import statements
        (if|elif|else|for|while|try|except|finally|with|def|class|return|
         yield|raise|break|continue|pass|assert|lambda|global|nonlocal)\b
    )
    """,
    re.VERBOSE,
)

# Things that look like prose: end in a period+space, start lower-case word
# followed by more plain words, contain common English filler words, etc.
PROSE_HINTS = re.compile(
    r"^(TODO|FIXME|NOTE|XXX|HACK|WARNING|NB)\b|"
    r"\b(the|this|that|because|should|note|todo|fixme|see|e\.g|i\.e|"
    r"please|need|needs|needed|use|using|used)\b",
    re.IGNORECASE,
)

# A line that is *only* punctuation/separators (e.g. "# ----------" or "# ====")
SEPARATOR_LINE = re.compile(r"^[\-=#\*~_]{2,}$")


def looks_like_code(comment_text: str) -> bool:
    """
    Decide whether the text of a comment (with the leading '#' stripped)
    looks like commented-out Python code rather than a natural-language
    comment.
    """
    text = comment_text.strip()

    if not text:
        return False

    # Skip shebangs, encoding declarations, and pure separator lines.
    if text.startswith("!") or "coding:" in text or "coding=" in text:
        return False
    if SEPARATOR_LINE.match(text):
        return False

    # Skip typical doc-comment markers.
    if PROSE_HINTS.match(text):
        return False

    # Must at least look syntactically code-like before we bother parsing.
    has_code_shape = bool(CODE_PATTERN.match(text))
    has_keyword = any(re.search(rf"\b{kw}\b", text) for kw in CODE_KEYWORDS)

    if not (has_code_shape or has_keyword):
        return False

    # Final check: does it actually parse as valid Python?
    # Try as a statement; if that fails, try wrapping common partials.
    candidates = [text]
    # Lines like "except ValueError:" or "else:" need a dummy body to parse
    if text.rstrip().endswith(":"):
        candidates.append(text + " pass")

    for candidate in candidates:
        try:
            tree = ast.parse(candidate)
        except SyntaxError:
            continue
        if not tree.body:
            continue
        # Reject trivial parses that are just a bare Name, Constant, or
        # Attribute access with no call/operator — these are usually
        # prose that coincidentally parses (e.g. "# example", "# foo.bar").
        node = tree.body[0]
        if isinstance(node, ast.Expr):
            value = node.value
            if isinstance(value, (ast.Name, ast.Constant)):
                continue
            if isinstance(value, ast.Attribute) and not has_keyword:
                continue
        return True

    return False


@dataclass
class CommentLine:
    line_no: int
    text: str  # comment text with leading '#'(s) stripped, original spacing kept
    full_line: str


def get_indent(line: str) -> str:
    """Return the leading whitespace of a line."""
    return line[: len(line) - len(line.lstrip())]


def build_comment_runs(comment_lines, max_gap: int = 0):
    """
    Group raw COMMENT tokens into "runs": maximal sequences of comment
    lines that are contiguous in the source (allowing up to `max_gap`
    non-comment lines between them, default 0 = strictly consecutive
    line numbers). This is purely structural — it doesn't look at
    *content* yet. A run is the candidate unit we later decide is "code"
    or "prose" as a whole, which is what lets a block like:

        # except Exception as exc:
        #     print_error(
        #         f"...{exc}"
        #     )
        #     console.print_exception(...)

    get treated as one thing, even though lines like the bare f-string
    or the lone closing paren wouldn't individually look code-shaped.

    comment_lines: list of CommentLine, already sorted by line_no.
    """
    if not comment_lines:
        return []

    runs = []
    current = [comment_lines[0]]

    for cl in comment_lines[1:]:
        prev = current[-1]
        if cl.line_no - prev.line_no <= max_gap + 1:
            current.append(cl)
        else:
            runs.append(current)
            current = [cl]
    runs.append(current)
    return runs


def run_looks_like_code(run) -> bool:
    """
    Decide whether an entire comment run (one or more contiguous comment
    lines) represents commented-out code, by looking at the run as a
    whole rather than line-by-line. A run is flagged as code if:

      - any single line in it independently looks like code (the
        original per-line heuristic), OR
      - the lines in the run, joined together, parse as valid Python
        once dedented — this catches blocks where each individual line
        is innocuous (a bare string, a lone ')', a dict-key line) but
        the block as a whole is clearly a code fragment.
    """
    texts = [cl.text.strip() for cl in run]
    non_empty = [t for t in texts if t]
    if not non_empty:
        return False

    # Separator-only runs (e.g. a row of "# ----") are never code.
    if all(SEPARATOR_LINE.match(t) for t in non_empty):
        return False

    # Fast path: any individual line already looks like code.
    if any(looks_like_code(t) for t in texts):
        return True

    # Slow path: try to parse the whole run as a single block. Strip a
    # single leading '#' from any lines that still have one (defensive;
    # extract_comment_tokens already strips it, but nested "# #" comments
    # leave an extra one behind), then dedent and attempt ast.parse.
    candidate_lines = [t.lstrip("#") for t in texts]

    # Normalize indentation: find the minimum indent among non-blank
    # lines and strip it, so a block that was indented in the original
    # file (e.g. inside a function) still parses as top-level statements.
    non_blank = [line for line in candidate_lines if line.strip()]
    if not non_blank:
        return False
    min_indent = min(len(line) - len(line.lstrip()) for line in non_blank)
    dedented = "\n".join(
        line[min_indent:] if len(line) >= min_indent else line
        for line in candidate_lines
    )

    try:
        tree = ast.parse(dedented)
    except SyntaxError:
        return False

    if not tree.body:
        return False

    # Require at least one "interesting" statement (not just a bare
    # Expr/Name/Constant) so prose that happens to parse doesn't count.
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Call,
                ast.Assign,
                ast.AugAssign,
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.With,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Return,
                ast.Raise,
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            return True

    return False


@dataclass
class Finding:
    line_no: int  # primary/first line number (used for highlighting & sorting)
    comment_text: (
        str  # representative comment text (first line's, for grouped findings)
    )
    full_line: str
    end_line_no: int = (
        None  # last line in the group; equals line_no for single-line findings
    )

    def __post_init__(self):
        if self.end_line_no is None:
            self.end_line_no = self.line_no

    @property
    def line_count(self) -> int:
        return self.end_line_no - self.line_no + 1


def merge_runs(runs, max_gap: int = 2):
    """
    When --group is set, additionally merge separate *flagged* runs that
    sit close together (within max_gap source lines), so e.g. a
    commented-out try/except split by one stray prose line still reports
    as a single block. Operates on already content-filtered runs.
    """
    if not runs:
        return []

    merged = [list(runs[0])]
    for run in runs[1:]:
        prev = merged[-1]
        if run[0].line_no - prev[-1].line_no <= max_gap + 1:
            prev.extend(run)
        else:
            merged.append(list(run))
    return merged


@dataclass
class FileResult:
    path: Path
    findings: list = field(default_factory=list)
    all_lines: list = field(default_factory=list)


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------


def extract_comment_tokens(source: str):
    """
    Yield (line_no, comment_text_without_hash) for every COMMENT token in
    the source, using the tokenize module so we correctly ignore '#'
    characters that appear inside strings.
    """
    results = []
    try:
        tokens = tokenize.generate_tokens(StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                line_no = tok.start[0]
                raw = tok.string  # includes leading '#'
                text = raw.lstrip("#")
                results.append((line_no, text))
    except tokenize.TokenizeError, IndentationError, SyntaxError:
        pass
    return results


def scan_file(path: Path, group: bool = False, group_gap: int = 2) -> FileResult:
    result = FileResult(path=path)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result

    result.all_lines = source.splitlines()

    comment_lines = []
    for line_no, text in extract_comment_tokens(source):
        full_line = (
            result.all_lines[line_no - 1]
            if 0 <= line_no - 1 < len(result.all_lines)
            else ""
        )
        comment_lines.append(
            CommentLine(line_no=line_no, text=text, full_line=full_line)
        )

    comment_lines.sort(key=lambda c: c.line_no)

    # Step 1: structural grouping — every maximal run of strictly
    # consecutive comment lines, regardless of content.
    runs = build_comment_runs(comment_lines, max_gap=0)

    # Step 2: content filtering — keep only runs that look like code.
    flagged_runs = [run for run in runs if run_looks_like_code(run)]

    if group:
        # Step 3: optionally merge nearby flagged runs together too.
        flagged_runs = merge_runs(flagged_runs, max_gap=group_gap)
        findings = []
        for run in flagged_runs:
            texts = [cl.text.strip() for cl in run if cl.text.strip()]
            combined_text = (
                " / ".join(texts) if len(texts) > 1 else (texts[0] if texts else "")
            )
            findings.append(
                Finding(
                    line_no=run[0].line_no,
                    end_line_no=run[-1].line_no,
                    comment_text=combined_text,
                    full_line=run[0].full_line,
                )
            )
        result.findings = findings
    else:
        # Ungrouped: still report one finding per *run* (not per raw
        # line) since a run is the smallest meaningful unit — reporting
        # the bare ')' on its own line as a separate finding from the
        # call it closes would be noise either way.
        findings = []
        for run in flagged_runs:
            texts = [cl.text.strip() for cl in run if cl.text.strip()]
            combined_text = (
                " / ".join(texts) if len(texts) > 1 else (texts[0] if texts else "")
            )
            findings.append(
                Finding(
                    line_no=run[0].line_no,
                    end_line_no=run[-1].line_no,
                    comment_text=combined_text,
                    full_line=run[0].full_line,
                )
            )
        result.findings = findings

    return result


def scan_directory(root: Path, extensions, group: bool = False, group_gap: int = 2):
    file_results = []
    paths = sorted(
        p for ext in extensions for p in root.rglob(f"*{ext}") if p.is_file()
    )
    # de-dup in case extensions overlap
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    for path in unique_paths:
        fr = scan_file(path, group=group, group_gap=group_gap)
        if fr.findings:
            file_results.append(fr)
    return file_results, len(unique_paths)


# --------------------------------------------------------------------------
# Display
# --------------------------------------------------------------------------


def display_finding(
    file_result: FileResult, finding: Finding, context: int, theme: str
):
    lines = file_result.all_lines
    total = len(lines)

    start = max(1, finding.line_no - context)
    end = min(total, finding.end_line_no + context)

    snippet = "\n".join(lines[start - 1 : end])

    highlighted = set(range(finding.line_no, finding.end_line_no + 1))

    syntax = Syntax(
        snippet,
        "python",
        theme=theme,
        line_numbers=True,
        start_line=start,
        highlight_lines=highlighted,
        word_wrap=False,
        background_color="default",
    )

    header = Text()
    header.append("\U0001f4c4 ", style="bold")
    header.append(str(file_result.path), style="scan.path")
    header.append("  :", style="scan.dim")
    if finding.line_count > 1:
        header.append(f"{finding.line_no}-{finding.end_line_no}", style="scan.lineno")
        header.append(f"  ({finding.line_count} lines)", style="scan.dim italic")
    else:
        header.append(f"{finding.line_no}", style="scan.lineno")

    subtitle_label = (
        "commented code block" if finding.line_count > 1 else "commented code"
    )
    subtitle_text = finding.comment_text
    if len(subtitle_text) > 90:
        subtitle_text = subtitle_text[:87] + "..."

    console.print(
        Panel(
            syntax,
            title=header,
            title_align="left",
            border_style="scan.accent",
            subtitle=f"[scan.dim]{subtitle_label}: [/scan.dim][scan.bad]{subtitle_text}[/scan.bad]",
            subtitle_align="left",
            padding=(0, 1),
        )
    )
    console.print()


def display_summary(file_results, total_files_scanned, grouped: bool):
    total_findings = sum(len(fr.findings) for fr in file_results)
    total_lines = sum(f.line_count for fr in file_results for f in fr.findings)

    table = Table(
        title="Scan Summary",
        show_lines=False,
        header_style="scan.header.bg",
        border_style="scan.dim",
        title_style="scan.title",
    )
    table.add_column("File", style="scan.path", overflow="fold")
    if grouped:
        table.add_column("Blocks", justify="right", style="scan.lineno")
        table.add_column("Lines", justify="right", style="scan.dim")
    else:
        table.add_column("Occurrences", justify="right", style="scan.lineno")

    for fr in file_results:
        if grouped:
            lines_in_file = sum(f.line_count for f in fr.findings)
            table.add_row(str(fr.path), str(len(fr.findings)), str(lines_in_file))
        else:
            table.add_row(str(fr.path), str(len(fr.findings)))

    console.print(table)

    if grouped:
        console.print(
            f"\n[bold]Scanned[/bold] [scan.ok]{total_files_scanned}[/scan.ok] file(s), "
            f"found [scan.bad]{total_findings}[/scan.bad] commented-out code block(s) "
            f"({total_lines} line(s) total) across [scan.bad]{len(file_results)}[/scan.bad] file(s).\n"
        )
    else:
        console.print(
            f"\n[bold]Scanned[/bold] [scan.ok]{total_files_scanned}[/scan.ok] file(s), "
            f"found [scan.bad]{total_findings}[/scan.bad] commented-out code line(s) "
            f"across [scan.bad]{len(file_results)}[/scan.bad] file(s).\n"
        )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Scan a directory recursively for commented-out Python code."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--context",
        "-c",
        type=int,
        default=3,
        help="Number of surrounding lines to show before/after the match (default: 3)",
    )
    parser.add_argument(
        "--ext",
        action="append",
        default=None,
        help="File extension(s) to scan (default: .py). Can be repeated.",
    )
    parser.add_argument(
        "--group",
        "-g",
        action="store_true",
        help="Group adjacent/consecutive commented-out code lines into a single "
        "block finding instead of reporting each line separately. Lines within "
        "--group-gap source lines of each other are merged into the same block "
        "regardless of indentation, since real commented-out blocks often mix "
        "indent levels (if/else, function bodies, etc).",
    )
    parser.add_argument(
        "--group-gap",
        type=int,
        default=2,
        help="Max number of non-flagged source lines allowed between two flagged "
        "lines for them to still be merged into the same block when --group is "
        "set (default: 2).",
    )
    parser.add_argument(
        "--theme",
        default="ansi_dark",
        help="Syntax highlighting theme. Use 'ansi_dark' or 'ansi_light' to "
        "inherit your terminal's own ANSI palette, or any pygments theme "
        "name such as 'gruvbox-dark' (default: ansi_dark).",
    )
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        console.print(f"[scan.bad]Error:[/scan.bad] {root} is not a directory.")
        sys.exit(1)

    extensions = args.ext or [".py"]

    console.print(
        Rule(
            f"[scan.title]Scanning [scan.path]{root}[/scan.path] for commented-out Python code[/scan.title]"
        )
    )
    console.print()

    with console.status("[scan.ok]Scanning files...", spinner="dots"):
        file_results, total_files = scan_directory(
            root, extensions, group=args.group, group_gap=args.group_gap
        )

    if not file_results:
        console.print(
            Panel(
                "[scan.ok]No commented-out code found.[/scan.ok] \u2713",
                border_style="scan.ok",
            )
        )
        console.print(f"\nScanned {total_files} file(s).")
        return

    for fr in file_results:
        console.print(Rule(f"[scan.path]{fr.path}[/scan.path]", style="cyan"))
        for finding in fr.findings:
            display_finding(fr, finding, args.context, args.theme)

    console.print(Rule("[scan.title]Summary[/scan.title]"))
    display_summary(file_results, total_files, grouped=args.group)


if __name__ == "__main__":
    main()
