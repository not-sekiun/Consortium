import textwrap
from datetime import UTC, datetime

from rich.console import Console
from rich.text import Text


# Exports rich formatted text with color markup codes as ANSI escape sequences.
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
def format_argparse_epilog(epilog_str: str) -> str:
    return textwrap.dedent(epilog_str) + " "


# Format the color of agent generator status strings to be rendered by rich's console.
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


# Format the color of listener status strings to be rendered by rich's console.
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


# Format the color of agent generator build step status strings to be rendered by rich's
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


def format_agent_result_status_string_with_color(
    status_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "SUCCESS": "[bold green]SUCCESS[/]",
        "FAILURE": "[bold red]FAILURE[/]",
        "ERROR": "[bold white on red]ERROR[/]",
    }

    if status_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[status_str]
    return status_str


def format_agent_task_status_string_with_color(
    status_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "QUEUED": "[bold cyan]QUEUED[/]",
        "RUNNING": "[bold yellow]RUNNING[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
    }

    if status_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[status_str]
    return status_str


def format_snake_case_to_title(snake_case_str: str) -> str:
    return " ".join([word.capitalize() for word in snake_case_str.split("_")])


def format_dict_as_multi_line_key_value_string(
    input_dict: dict, display_value_as_repr: bool = True
) -> str:
    if not input_dict:
        return ""

    max_key_length = max(len(key) for key in input_dict.keys())
    formatted_strings = []
    for key, value in input_dict.items():
        if display_value_as_repr:
            formatted_strings.append(f"• {key:<{max_key_length}} : {value!r}")
        else:
            formatted_strings.append(f"• {key:<{max_key_length}} : {value}")
    return "\n".join(formatted_strings)


def format_dict_as_single_line_key_value_string(input_dict: dict) -> str:
    formatted_strings = []
    for key, value in input_dict.items():
        formatted_strings.append(f"{key}={value!r}")
    return ", ".join(formatted_strings)


def format_list_as_multi_line_bulleted_string(input_list: list) -> str:
    if not input_list:
        return ""

    formatted_strings = []
    for item in input_list:
        formatted_strings.append(f"• {item}")
    return "\n".join(formatted_strings)


def format_size_bytes_as_human_readable_str(size_bytes: int):
    if size_bytes == 0:
        return "0 B"
    # IEC Standard (Binary)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"


def format_seconds_as_human_readable_str(seconds: float) -> str:
    if seconds <= 0:
        return "0s"

    # Very short durations: keep precision
    if seconds < 60:
        return f"{seconds:.2f}s".rstrip("0").rstrip(".")

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: list[str] = []

    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")

    # For durations over a minute, seconds are rounded and optional
    if int(secs) > 0 and not parts:
        # Only include seconds if nothing else was shown (e.g. 1m 0s → 1m)
        parts.append(f"{int(secs)}s")

    return " ".join(parts)


def format_datetime_as_human_readable_str(
    datetime_str: str, include_elapsed_time: bool = False
) -> str:
    datetime_obj = datetime.fromisoformat(datetime_str)
    datetime_obj = datetime_obj.astimezone(UTC)
    elapsed_seconds = (datetime.now(UTC) - datetime_obj).total_seconds()

    if include_elapsed_time:
        datetime_to_nearest_second = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{datetime_to_nearest_second} "
            f"({format_seconds_as_human_readable_str(elapsed_seconds)} ago)"
        )
    else:
        return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
