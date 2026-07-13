import textwrap
from collections.abc import Callable
from typing import Any


def remap_exception(
    original_exception: Exception,
    original_kwargs: dict[str, Any],
    exception_map: dict[type[Exception], type[Exception]],
    exception_kwargs_map: dict[str, str],
) -> BaseException:
    remapped_kwargs = {
        exception_kwargs_map.get(k, k): v for k, v in original_kwargs.items()
    }
    remapped_exception_class = exception_map[type(original_exception)]
    return remapped_exception_class(**remapped_kwargs)


# Automatically "intelligently" formats indented docstrings to a single line string by
# replacing newline characters with empty spaces if a line ends with a space or
# automatically adding a space if the newline does not end with a space.
def format_docstring_to_single_line(docstring: str) -> str:
    dedented_docstring = textwrap.dedent(docstring)
    single_line_string = ""
    for line in dedented_docstring.splitlines():
        if line.endswith(" "):
            single_line_string += line
        else:
            single_line_string += line + " "

    return single_line_string.strip()


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
