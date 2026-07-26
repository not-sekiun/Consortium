import sys
import textwrap
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import ValidationError

# Reported in place of a module filepath when a component's declaring module was not
# loaded from disk and in place of a parameter type that could not be resolved.
_UNKNOWN_PARAMETER_TYPE = "unknown"


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
    validating_function: Callable[[Any], None] | None,
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


def resolve_component_filepath(cls: type) -> str:
    # A module assembled at runtime rather than imported from disk has no `__file__`,
    # so fall back to the module name to keep the component identifiable in errors.
    module = sys.modules.get(cls.__module__)
    filepath = getattr(module, "__file__", None)

    return filepath if filepath is not None else f"<module {cls.__module__}>"


def _format_validation_error_location(location: Sequence[str | int]) -> str:
    # Pydantic reports the path to an offending value as a tuple where string entries
    # name a field or mapping key and integer entries index into a sequence. Those are
    # rendered as attribute access and subscript access respectively, so a location of
    # `("options", 0, "name")` formats as `options[0].name`.
    formatted_location = ""
    for entry in location:
        if isinstance(entry, int):
            formatted_location += f"[{entry}]"
        elif formatted_location:
            formatted_location += f".{entry}"
        else:
            formatted_location = entry

    return formatted_location


def resolve_validation_error_parameter(
    exc: ValidationError,
    parameter_types: Mapping[str, Any],
    fallback_parameter_name: str = "",
) -> tuple[str, str]:
    errors = exc.errors()
    location = errors[0]["loc"] if errors else ()
    parameter_name = (
        _format_validation_error_location(location=location) or fallback_parameter_name
    )
    # Only the first entry of the location names a top level parameter, so the type
    # lookup uses that while the reported name keeps the full path to the value.
    top_level_parameter_name = str(location[0]) if location else fallback_parameter_name
    parameter_type = parameter_types.get(top_level_parameter_name)

    return parameter_name, (
        _UNKNOWN_PARAMETER_TYPE if parameter_type is None else str(parameter_type)
    )
