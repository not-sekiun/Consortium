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
    agent_generator_state_string: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold red on white]FATAL[/]",
    }

    if agent_generator_state_string in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[agent_generator_state_string]
    return agent_generator_state_string


# Format the color of listener state strings to be rendered by rich's console.
def format_listener_state_string_with_color(
    listener_state_string: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold green]RUNNING[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold red on white]FATAL[/]",
    }
    if listener_state_string in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[listener_state_string]
    return listener_state_string


# Format the color of agent generator build step state strings to be rendered by rich's
# console.
def format_agent_generator_build_step_state_string_with_color(
    agent_generator_build_step_state_string: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold red on white]FATAL[/]",
    }

    if (
        agent_generator_build_step_state_string
        in state_string_to_colored_state_string_map
    ):
        return state_string_to_colored_state_string_map[
            agent_generator_build_step_state_string
        ]
    return agent_generator_build_step_state_string


def format_agent_result_state_string_with_color(
    agent_result_state_string: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "SUCCESS": "[bold green]SUCCESS[/]",
        "FAILED": "[bold red]FAILED[/]",
        "ERRORED": "[bold red on white]ERRORED[/]",
    }

    if agent_result_state_string in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[agent_result_state_string]
    return agent_result_state_string


def format_agent_task_state_string_with_color(
    agent_task_state_string: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
    }

    if agent_task_state_string in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[agent_task_state_string]
    return agent_task_state_string


def format_snake_case_to_title(snake_case_string: str) -> str:
    return " ".join([word.capitalize() for word in snake_case_string.split("_")])
