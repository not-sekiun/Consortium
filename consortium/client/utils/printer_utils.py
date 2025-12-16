from rich.console import Console

# Rich console instance for the client to use for printing.
CONSOLE = Console()


def print_success(*args, highlight: bool | None = False, **kwargs):
    CONSOLE.print("[bold green][+][/bold green]", end=" ")
    CONSOLE.print(*args, highlight=highlight, **kwargs)


def print_error(*args, highlight: bool | None = False, **kwargs):
    CONSOLE.print("[bold red][-][/bold red]", end=" ")
    CONSOLE.print(*args, highlight=highlight, **kwargs)


def print_info(*args, highlight: bool | None = False, **kwargs):
    CONSOLE.print("[bold blue][*][/bold blue]", end=" ")
    CONSOLE.print(*args, highlight=highlight, **kwargs)


def print_warning(*args, highlight: bool | None = False, **kwargs):
    CONSOLE.print("[bold yellow][!][/bold yellow]", end=" ")
    CONSOLE.print(*args, highlight=highlight, **kwargs)
