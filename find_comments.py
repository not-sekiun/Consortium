#!/usr/bin/env python3
"""
find_dead_code.py — Recursively scan a directory for Python files containing
commented-out code (as opposed to ordinary natural-language comments), and
display each finding with file path, line number, and surrounding context,
nicely rendered with `rich`.

Usage:
    python find_dead_code.py [DIRECTORY] [--context N] [--ext .py] [--group]

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

console = Console()


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


def get_indent(line: str) -> str:
    """Return the leading whitespace of a line (used to keep grouped
    comments aligned at the same indentation level)."""
    return line[: len(line) - len(line.lstrip())]


def group_adjacent_findings(raw_findings, all_lines, max_gap: int = 1):
    """
    Merge consecutive flagged comment lines into a single Finding spanning
    a range, so a multi-line block of commented-out code (e.g. each line
    prefixed with its own '#') is reported once instead of once per line.

    Two flagged lines are merged if:
      - they are within `max_gap` lines of each other (default: adjacent,
        i.e. gap of 1 means line N and N+1 merge; a blank/non-flagged
        line in between breaks the group), and
      - they share the same leading indentation (so a comment at one
        indent level doesn't swallow a differently-indented one below it).

    raw_findings: list of Finding, each representing a single flagged line,
                  already sorted by line_no.
    """
    if not raw_findings:
        return []

    grouped = []
    current_group = [raw_findings[0]]

    def indent_of(finding):
        return get_indent(finding.full_line)

    for finding in raw_findings[1:]:
        prev = current_group[-1]
        same_indent = indent_of(finding) == indent_of(prev)
        adjacent = (finding.line_no - prev.line_no) <= max_gap

        if same_indent and adjacent:
            current_group.append(finding)
        else:
            grouped.append(current_group)
            current_group = [finding]

    grouped.append(current_group)

    merged_findings = []
    for group in grouped:
        first = group[0]
        last = group[-1]
        # Representative comment text: join each line's comment text with
        # a newline so the subtitle can show the whole block if desired.
        combined_text = (
            " / ".join(f.comment_text for f in group)
            if len(group) > 1
            else first.comment_text
        )
        merged_findings.append(
            Finding(
                line_no=first.line_no,
                end_line_no=last.line_no,
                comment_text=combined_text,
                full_line=first.full_line,
            )
        )

    return merged_findings


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
    Yield (line_no, comment_text_without_hash, full_source_line) for every
    COMMENT token in the source, using the tokenize module so we correctly
    ignore '#' characters that appear inside strings.
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
    except (tokenize.TokenizeError, IndentationError, SyntaxError):
        pass
    return results


def scan_file(path: Path, group: bool = False) -> FileResult:
    result = FileResult(path=path)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result

    result.all_lines = source.splitlines()
    raw_findings = []

    for line_no, comment_text in extract_comment_tokens(source):
        if looks_like_code(comment_text):
            full_line = (
                result.all_lines[line_no - 1]
                if 0 <= line_no - 1 < len(result.all_lines)
                else ""
            )
            raw_findings.append(
                Finding(
                    line_no=line_no,
                    comment_text=comment_text.strip(),
                    full_line=full_line,
                )
            )

    raw_findings.sort(key=lambda f: f.line_no)

    if group:
        result.findings = group_adjacent_findings(raw_findings, result.all_lines)
    else:
        result.findings = raw_findings

    return result


def scan_directory(root: Path, extensions, group: bool = False):
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
        fr = scan_file(path, group=group)
        if fr.findings:
            file_results.append(fr)
    return file_results, len(unique_paths)


# --------------------------------------------------------------------------
# Display
# --------------------------------------------------------------------------


def display_finding(file_result: FileResult, finding: Finding, context: int):
    lines = file_result.all_lines
    total = len(lines)

    start = max(1, finding.line_no - context)
    end = min(total, finding.end_line_no + context)

    snippet = "\n".join(lines[start - 1 : end])

    highlighted = set(range(finding.line_no, finding.end_line_no + 1))

    syntax = Syntax(
        snippet,
        "python",
        theme="monokai",
        line_numbers=True,
        start_line=start,
        highlight_lines=highlighted,
        word_wrap=False,
        background_color="default",
    )

    header = Text()
    header.append("📄 ", style="bold")
    header.append(str(file_result.path), style="bold cyan")
    header.append("  :", style="dim")
    if finding.line_count > 1:
        header.append(f"{finding.line_no}-{finding.end_line_no}", style="bold yellow")
        header.append(f"  ({finding.line_count} lines)", style="dim italic")
    else:
        header.append(f"{finding.line_no}", style="bold yellow")

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
            border_style="bright_magenta",
            subtitle=f"[dim]{subtitle_label}: [/dim][red]{subtitle_text}[/red]",
            subtitle_align="left",
            padding=(0, 1),
        )
    )
    console.print()


def display_summary(file_results, total_files_scanned, grouped: bool):
    total_findings = sum(len(fr.findings) for fr in file_results)
    total_lines = sum(f.line_count for fr in file_results for f in fr.findings)

    table = Table(
        title="Scan Summary", show_lines=False, header_style="bold white on dark_blue"
    )
    table.add_column("File", style="cyan", overflow="fold")
    if grouped:
        table.add_column("Blocks", justify="right", style="bold yellow")
        table.add_column("Lines", justify="right", style="dim")
    else:
        table.add_column("Occurrences", justify="right", style="bold yellow")

    for fr in file_results:
        if grouped:
            lines_in_file = sum(f.line_count for f in fr.findings)
            table.add_row(str(fr.path), str(len(fr.findings)), str(lines_in_file))
        else:
            table.add_row(str(fr.path), str(len(fr.findings)))

    console.print(table)

    if grouped:
        console.print(
            f"\n[bold]Scanned[/bold] [green]{total_files_scanned}[/green] file(s), "
            f"found [bold red]{total_findings}[/bold red] commented-out code block(s) "
            f"({total_lines} line(s) total) across [bold red]{len(file_results)}[/bold red] file(s).\n"
        )
    else:
        console.print(
            f"\n[bold]Scanned[/bold] [green]{total_files_scanned}[/green] file(s), "
            f"found [bold red]{total_findings}[/bold red] commented-out code line(s) "
            f"across [bold red]{len(file_results)}[/bold red] file(s).\n"
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
        help="Group adjacent/consecutive commented-out code lines (same indent, "
        "no gap) into a single block finding instead of reporting each "
        "line separately.",
    )
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        console.print(f"[bold red]Error:[/bold red] {root} is not a directory.")
        sys.exit(1)

    extensions = args.ext or [".py"]

    console.print(
        Rule(f"[bold]Scanning [cyan]{root}[/cyan] for commented-out Python code[/bold]")
    )
    console.print()

    with console.status("[bold green]Scanning files...", spinner="dots"):
        file_results, total_files = scan_directory(root, extensions, group=args.group)

    if not file_results:
        console.print(
            Panel(
                "[green]No commented-out code found.[/green] ✅",
                border_style="green",
            )
        )
        console.print(f"\nScanned {total_files} file(s).")
        return

    for fr in file_results:
        console.print(Rule(f"[bold cyan]{fr.path}[/bold cyan]", style="cyan"))
        for finding in fr.findings:
            display_finding(fr, finding, args.context)

    console.print(Rule("[bold]Summary[/bold]"))
    display_summary(file_results, total_files, grouped=args.group)


if __name__ == "__main__":
    main()
