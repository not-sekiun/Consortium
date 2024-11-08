from typing import Any, Callable

from consortium.server.utils.formatter_utils import format_docstring_to_single_line


def resolve_validating_function_string(
    validating_function: Callable[[Any], None],
) -> str | None:
    # If a validating function is present, we want to display the docstring
    # of the function in the JSON output. If the function does not have a docstring, we
    # will display an empty string.
    if validating_function:
        if validating_function.__doc__:
            return format_docstring_to_single_line(
                docstring=validating_function.__doc__,
            )
        else:
            return ""
    # If no `validating_function` function is present, we will return `None` for the
    # corresponding JSON output.
    else:
        return None
