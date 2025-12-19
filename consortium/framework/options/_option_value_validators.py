import re
from collections.abc import Callable
from typing import Any

from consortium.framework.framework_types import Primitive
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)


def validate_value_data_type(
    option_name: str,
    option_value: Any,
    *value_types: type,
) -> None:
    if not isinstance(option_value, value_types):
        if len(value_types) == 1:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be of type "
                f"'{value_types[0]}'.",
            )
        else:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be of one of "
                "the following types: "
                f"{', '.join([str(value_type) for value_type in value_types])}.",
            )


def validate_value_string_length(
    option_name: str,
    option_value: Primitive,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    if isinstance(option_value, str):
        if minimum_length is not None and len(option_value) < minimum_length:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must have a "
                f"minimum length of {minimum_length}.",
            )
        if maximum_length is not None and len(option_value) > maximum_length:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must have a "
                f"maximum length of {maximum_length}.",
            )


def validate_value_numeric_range(
    option_name: str,
    option_value: Primitive,
    greater_than: int | float | None,
    less_than: int | float | None,
    greater_than_or_equal_to: int | float | None,
    less_than_or_equal_to: int | float | None,
) -> None:
    if isinstance(option_value, (int, float)):
        if greater_than is not None and option_value <= greater_than:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be greater "
                f"than {greater_than}.",
            )
        if less_than is not None and option_value >= less_than:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be lesser "
                f"than {less_than}.",
            )
        if (
            greater_than_or_equal_to is not None
            and option_value < greater_than_or_equal_to
        ):
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be greater "
                f"than or equal to {greater_than_or_equal_to}.",
            )
        if less_than_or_equal_to is not None and option_value > less_than_or_equal_to:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must be lesser "
                f"than or equal to {less_than_or_equal_to}.",
            )


def validate_value_regex_format(
    option_name: str,
    option_value: Primitive,
    validating_regex: str | None,
) -> None:
    if validating_regex:
        if not re.match(validating_regex, str(option_value)):
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' must match the "
                f"regex pattern: {validating_regex}.",
            )


def validate_value_on_validating_function(
    option_name: str,
    option_value: Primitive,
    validating_function: Callable | None,
) -> None:
    if validating_function:
        try:
            validating_function(option_value)
        except Exception as exc:
            raise OptionValueValidationError(
                f"Value '{option_value}' for option '{option_name}' failed against its "
                f"validating function: {exc}",
            ) from None


def validate_iterable_value_length(
    option_name: str,
    option_value: list[Primitive] | dict[str, Primitive],
    minimum_elements: int | None,
    maximum_elements: int | None,
) -> None:
    if minimum_elements is not None and len(option_value) < minimum_elements:
        raise OptionValueValidationError(
            f"Option '{option_name}' has {len(option_value)} element(s) but must have "
            f"a minimum number of {minimum_elements} element(s).",
        )
    if maximum_elements is not None and len(option_value) > maximum_elements:
        raise OptionValueValidationError(
            f"Option '{option_name}' has {len(option_value)} element(s) but must have "
            f"a maximum number of {maximum_elements} element(s).",
        )


def validate_iterable_element_duplication(
    option_name: str,
    option_value: list[Primitive],
    allow_duplicates: bool,
) -> None:
    if not allow_duplicates:
        unique_elements = set()
        for element in option_value:
            if element in unique_elements:
                raise OptionValueValidationError(
                    f"Element '{element}' in list value for option '{option_name}' "
                    f"contains duplicate copies while the option disallows "
                    "duplicate elements.",
                )
            unique_elements.add(element)
