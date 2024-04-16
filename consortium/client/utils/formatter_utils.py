from rich.console import Console
from rich.text import Text


def export_rich_text_as_ansi(text: Text | str) -> str:
    console = Console()
    with console.capture() as capture:
        console.print(text, end="")
    return capture.get()
