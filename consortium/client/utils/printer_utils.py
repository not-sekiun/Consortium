from rich.console import Console
from rich.text import Text

# Global Rich console instance for the client to use for printing.
console = Console()


def print_success(*args, **kwargs):
    status_prefix = Text("[+]", style="bold green", end="")
    console.print(status_prefix, *args, **kwargs)


def print_error(
    *args, exc: Exception | None = None, exc_cause_depth: int = 2, **kwargs
):
    status_prefix = Text("[-]", style="bold red", end="")
    console.print(status_prefix, *args, **kwargs)

    if exc is not None:
        depth = 0
        indent_char = "[red]╰─[/]"

        while exc is not None and depth < exc_cause_depth:
            exc_message = f": {exc}" if str(exc) else ""
            console.print(
                f"    {'   ' * depth}{indent_char} [red]{type(exc).__name__}[/]{exc_message}"
            )
            exc = exc.__cause__
            depth += 1

        remaining_exc_count = 0
        while exc is not None:
            remaining_exc_count += 1
            exc = exc.__cause__
        if remaining_exc_count > 0:
            console.print(
                f"    {'   ' * depth}... and {remaining_exc_count} more exception(s)"
            )


def print_info(*args, **kwargs):
    status_prefix = Text("[*]", style="bold blue", end="")
    console.print(status_prefix, *args, **kwargs)


def print_warning(*args, **kwargs):
    status_prefix = Text("[!]", style="bold yellow", end="")
    console.print(status_prefix, *args, **kwargs)
