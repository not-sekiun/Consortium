import textwrap

from rich.console import Console
from rich.text import Text


# Exports rich text with color markup codes as ANSI escape sequences.
def format_rich_text_as_ansi(text: Text | str) -> str:
    console = Console()
    with console.capture() as capture:
        console.print(text, end="")
    return capture.get()


# Provides a wrapper around textwrap.dedent to allow for formatting of argparse epilog
# strings in source code without effecting the formatting of the string when it is
# displayed in the help menu. Additionally, a single whitespace character is appended at
# the end to ensure that the epilog is displayed with a newline character at the end,
# else argparse simply ignores that last newline character.
def format_argparse_epilog(epilog_string: str) -> str:
    return textwrap.dedent(epilog_string) + " "


# Format the color of agent generator state strings to be rendered by rich's console.
def format_agent_generator_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold white on red]FATAL[/]",
    }

    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


# Format the color of listener state strings to be rendered by rich's console.
def format_listener_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold green]RUNNING[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold white on red]FATAL[/]",
    }
    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


# Format the color of agent generator build step state strings to be rendered by rich's
# console.
def format_agent_generator_build_step_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold white on red]FATAL[/]",
    }

    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


def format_agent_result_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "SUCCESS": "[bold green]SUCCESS[/]",
        "FAILED": "[bold red]FAILED[/]",
        "ERRORED": "[bold white on red]ERRORED[/]",
    }

    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


def format_agent_task_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
    }

    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


def format_snake_case_to_title(snake_case_str: str) -> str:
    return " ".join([word.capitalize() for word in snake_case_str.split("_")])
