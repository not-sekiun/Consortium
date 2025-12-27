from rich.console import Console

# Rich console instance for the client to use for printing.
CONSOLE = Console(highlight=True)


def print_success(*args, **kwargs):
    CONSOLE.print("[bold green][+][/bold green]", end=" ")
    CONSOLE.print(*args, **kwargs)


def print_error(*args, **kwargs):
    CONSOLE.print("[bold red][-][/bold red]", end=" ")
    CONSOLE.print(*args, **kwargs)


def print_info(*args, **kwargs):
    CONSOLE.print("[bold blue][*][/bold blue]", end=" ")
    CONSOLE.print(*args, **kwargs)


def print_warning(*args, **kwargs):
    CONSOLE.print("[bold yellow][!][/bold yellow]", end=" ")
    CONSOLE.print(*args, **kwargs)
