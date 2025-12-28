from rich.console import Console
from rich.text import Text

# Global Rich console instance for the client to use for printing.
console = Console()


def print_success(*args, **kwargs):
    status_prefix = Text("[+]", style="bold green", end="")
    console.print(status_prefix, *args, **kwargs)


def print_error(*args, **kwargs):
    status_prefix = Text("[-]", style="bold red", end="")
    console.print(status_prefix, *args, **kwargs)


def print_info(*args, **kwargs):
    status_prefix = Text("[*]", style="bold blue", end="")
    console.print(status_prefix, *args, **kwargs)


def print_warning(*args, **kwargs):
    status_prefix = Text("[!]", style="bold yellow", end="")
    console.print(status_prefix, *args, **kwargs)
