from rich.console import Console

# Global Rich console instance for the client to use for printing.
console = Console()


def print_success(*args, **kwargs):
    console.print("[bold green][+][/bold green]", end=" ")
    console.print(*args, **kwargs)


def print_error(*args, **kwargs):
    console.print("[bold red][-][/bold red]", end=" ")
    console.print(*args, **kwargs)


def print_info(*args, **kwargs):
    console.print("[bold blue][*][/bold blue]", end=" ")
    console.print(*args, **kwargs)


def print_warning(*args, **kwargs):
    console.print("[bold yellow][!][/bold yellow]", end=" ")
    console.print(*args, **kwargs)
