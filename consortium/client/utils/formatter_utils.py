import textwrap
from datetime import UTC, datetime
from typing import Any

from rich.console import Console


# Exports rich formatted text with color markup codes as ANSI escape sequences.
def format_rich_text_as_ansi(text: str) -> str:
    console = Console()
    with console.capture() as capture:
        console.print(text, end="")
    return capture.get()


# Applies rich's default highlight styling, used everywhere in the client, to the given
# text and exports it as ANSI escape sequences.
def format_object_as_rich_ansi_highlight_str(value: Any) -> str:
    console = Console()
    with console.capture() as capture:
        console.print(value, end="", highlight=True)
    return capture.get()


# Provides a wrapper around textwrap.dedent to allow for formatting of argparse epilog
# strings in source code without effecting the formatting of the string when it is
# displayed in the help menu. Additionally, a single whitespace character is appended at
# the end to ensure that the epilog is displayed with a newline character at the end,
# else argparse simply ignores that last newline character.
def format_argparse_epilog(epilog_str: str) -> str:
    return textwrap.dedent(epilog_str) + " "


# Format the color of listener status strings to be rendered by rich's console.
def format_listener_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "INITIALIZED": "[bold cyan]INITIALIZED[/]",
        "STARTED": "[bold yellow]STARTED[/]",
        "RUNNING": "[bold green]RUNNING[/]",
        "STOPPING": "[bold yellow]STOPPING[/]",
        "STOPPED": "[bold cyan]STOPPED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold white on red]FATAL[/]",
        "COMPLETED": "[bold cyan]COMPLETED[/]",
    }

    if state_str in state_string_to_colored_state_string_map:
        return state_string_to_colored_state_string_map[state_str]
    return state_str


# Format the color of agent generator component status strings to be rendered by rich's
# console. This includes agent generators, and agent generator build steps.
def format_agent_generator_state_string_with_color(
    state_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "INITIALIZED": "[bold cyan]INITIALIZED[/]",
        "STARTED": "[bold yellow]STARTED[/]",
        "RUNNING": "[bold yellow]RUNNING[/]",
        "STOPPING": "[bold yellow]STOPPING[/]",
        "STOPPED": "[bold yellow]STOPPED[/]",
        "ERRORED": "[bold red]ERRORED[/]",
        "FATAL": "[bold white on red]FATAL[/]",
        "COMPLETED": "[bold green]COMPLETED[/]",
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


def format_agent_task_progress_status_string_with_color(
    status_str: str,
) -> str:
    state_string_to_colored_state_string_map = {
        "SUCCESS": "[bold green]SUCCESS[/]",
        "FAILURE": "[bold red]FAILURE[/]",
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


def format_list_as_single_line_comma_separated_string(input_list: list) -> str:
    return ", ".join(str(item) for item in input_list)


def format_mitre_attack_technique(mitre_attack_technique: dict[str, Any]) -> str:
    return (
        f"[bold blue]({format_list_as_single_line_comma_separated_string([tactic.upper() for tactic in mitre_attack_technique['tactics']])})[/] "
        f"[bold yellow]{mitre_attack_technique['mitre_attack_technique_id']}:[/] "
        f"[bold green]{mitre_attack_technique['name']}[/]"
    )


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
    datetime_str: str | datetime, include_elapsed_time: bool = False
) -> str:
    if isinstance(datetime_str, datetime):
        datetime_obj = datetime_str.astimezone(UTC)
    else:
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


def format_value_type_specification_epilog() -> str:
    return format_argparse_epilog(
        """
        Value Type Specification:
          Values are strings by default. Specify types using:
            1. Inline annotation: <value>:<type> (e.g., "3:int", "t:bool")
            2. --value-type flag: applies to all values, unless overridden by inline annotations
            3. Argument's default type: used when no type is specified

          Use --help-full for detailed usage examples.
        """,
    )


def format_value_type_specification_with_examples_epilog(example_prefix: str) -> str:
    return format_value_type_specification_epilog() + format_argparse_epilog(
        f"""
        Examples:
          # Single values
          {example_prefix} 1              # String "1" (or option's default type)
          {example_prefix} 1:int          # Integer 1
          {example_prefix} 1 -t int       # Integer 1 (equivalent)
          {example_prefix} text:str:str   # String "text:str" (escape colons)

          # Choice values
          {example_prefix} choice1        # Implicit type conversion
          {example_prefix} 1 -t int       # Exact match required (no conversion)

          # Lists
          {example_prefix} 1 2 3:int      # ["1", "2", 3]
          {example_prefix} 1 2 3 -t int   # [1, 2, 3]
          {example_prefix} 1 2 3:str -t int  # [1, 2, "3"]

          # Dictionaries
          {example_prefix} k1 1 k2 2:str -t int  # {{k1: 1, k2: "2"}}

          # Toggleable choices (default: toggle specified to True, rest to False)
          {example_prefix} c1 c2          # c1=True, c2=True, others=False
          {example_prefix} false:bool c1  # c1=False, others=True
          {example_prefix} true:bool      # All choices=True
          {example_prefix} t:bool         # All choices=True (t/f/1/0 accepted)
          {example_prefix} 0 -t bool      # All choices=False
        """,
    )


def format_role_str_with_color(role: str) -> str:
    role_str_to_colored_role_str_map = {
        "ADMIN": "[bold red]ADMIN[/]",
        "OPERATOR": "[bold green]OPERATOR[/]",
        "SPECTATOR": "[bold cyan]SPECTATOR[/]",
    }

    if role in role_str_to_colored_role_str_map:
        return role_str_to_colored_role_str_map[role]
    return role


def format_agent_status_string_with_color(
    status_str: str,
) -> str:
    status_string_to_colored_status_string_map = {
        "ACTIVE": "[bold green]ACTIVE[/]",
        "INACTIVE": "[bold yellow]INACTIVE[/]",
        "ORPHANED": "[bold magenta]ORPHANED[/]",
        "UNREACHABLE": "[bold red]UNREACHABLE[/]",
    }

    if status_str in status_string_to_colored_status_string_map:
        return status_string_to_colored_status_string_map[status_str]
    return status_str
