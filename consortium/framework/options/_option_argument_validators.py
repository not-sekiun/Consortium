import inspect
import re
from collections.abc import Callable
from typing import Any, Literal

from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    InvalidOptionConfigurationParameterTypeError,
    InvalidOptionIterableLengthBoundError,
    InvalidOptionIterableLengthRangeError,
    InvalidOptionValueLengthBoundError,
    InvalidOptionValueLengthRangeError,
    InvalidOptionValueRangeError,
    InvalidValidatingRegexError,
)


def validate_string_length_arguments(
    option_name: str,
    option_value_type: type,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    if minimum_length is not None or maximum_length is not None:
        if not issubclass(option_value_type, str):
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=option_name,
                error_message=(
                    "The parameters `minimum_length` and `maximum_length` are only "
                    "applicable to options with a value type of `str`."
                ),
            )
        if minimum_length is not None and minimum_length < 0:
            raise InvalidOptionValueLengthBoundError(
                option_name=option_name,
                length_bound_parameter_name="minimum_length",
                length_bound=minimum_length,
            )
        if maximum_length is not None and maximum_length < 0:
            raise InvalidOptionValueLengthBoundError(
                option_name=option_name,
                length_bound_parameter_name="maximum_length",
                length_bound=maximum_length,
            )
        if (maximum_length is not None and minimum_length is not None) and (
            maximum_length < minimum_length
        ):
            raise InvalidOptionValueLengthRangeError(
                option_name=option_name,
                minimum_length=minimum_length,
                maximum_length=maximum_length,
            )


def validate_numeric_range_arguments(
    option_name: str,
    option_value_type: type,
    greater_than: int | float | None,
    less_than: int | float | None,
    greater_than_or_equal_to: int | float | None,
    less_than_or_equal_to: int | float | None,
) -> None:
    parameters = {
        "greater_than": greater_than,
        "less_than": less_than,
        "greater_than_or_equal_to": greater_than_or_equal_to,
        "less_than_or_equal_to": less_than_or_equal_to,
    }

    for parameter_name, parameter_value in parameters.items():
        if parameter_value is not None and not issubclass(
            option_value_type, (int, float)
        ):
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=option_name,
                error_message=(
                    f"The parameter `{parameter_name}` is only applicable to options "
                    f"with a value type of `int` or `float`."
                ),
            )

    if greater_than is not None:
        if less_than is not None and greater_than > less_than:
            raise InvalidOptionValueRangeError(
                option_name=option_name,
                minimum_range_parameter_name="less_than",
                maximum_range_parameter_name="greater_than",
                minimum_range=less_than,
                maximum_range=greater_than,
            )
        if less_than_or_equal_to is not None and greater_than > less_than_or_equal_to:
            raise InvalidOptionValueRangeError(
                option_name=option_name,
                minimum_range_parameter_name="less_than_or_equal_to",
                maximum_range_parameter_name="greater_than",
                minimum_range=less_than_or_equal_to,
                maximum_range=greater_than,
            )
    if greater_than_or_equal_to is not None:
        if less_than is not None and greater_than_or_equal_to > less_than:
            raise InvalidOptionValueRangeError(
                option_name=option_name,
                minimum_range_parameter_name="less_than_or_equal_to",
                maximum_range_parameter_name="greater_than_or_equal_to",
                minimum_range=less_than_or_equal_to,
                maximum_range=greater_than_or_equal_to,
            )


def validate_validating_regex_argument(
    option_name: str,
    validating_regex: str | None,
    validating_regex_parameter_name: Literal[
        "validating_regex",
        "key_validating_regex",
        "value_validating_regex",
    ] = "validating_regex",
) -> None:
    if validating_regex is not None:
        if not isinstance(validating_regex, str):
            raise InvalidOptionConfigurationParameterTypeError(
                parameter_name=validating_regex_parameter_name,
                parameter_type="str",
                option_str=option_name,
            )
        try:
            re.compile(validating_regex)
        except re.error as exc:
            raise InvalidValidatingRegexError(
                option_name=option_name,
                validating_regex=validating_regex,
                regex_error_message=str(exc),
            ) from None


def validate_validating_function_argument(
    option_name: str,
    validating_function: Callable[[Any], None] | None,
    validating_function_parameter_name: Literal[
        "validating_function",
        "key_validating_function",
        "value_validating_function",
    ] = "validating_function",
) -> None:
    if validating_function is not None:
        if not isinstance(validating_function, Callable):
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=option_name,
                parameter_name=validating_function_parameter_name,
                parameter_type="callable",
            )
        function_signature = inspect.signature(validating_function)
        if len(function_signature.parameters) != 1:
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=option_name,
                error_message=(
                    f"The validating function parameter `{validating_function_parameter_name}` "
                    "must be a callable that accepts exactly one argument."
                ),
            )


def validate_iterable_length_arguments(
    option_name: str,
    minimum_elements: int | None,
    maximum_elements: int | None,
) -> None:
    if minimum_elements is not None and minimum_elements < 0:
        raise InvalidOptionIterableLengthBoundError(
            option_name=option_name,
            length_bound_parameter_name="minimum_elements",
            length_bound=minimum_elements,
        )
    if maximum_elements is not None and maximum_elements < 0:
        raise InvalidOptionIterableLengthBoundError(
            option_name=option_name,
            length_bound_parameter_name="maximum_elements",
            length_bound=maximum_elements,
        )
    if (maximum_elements is not None and minimum_elements is not None) and (
        maximum_elements < minimum_elements
    ):
        raise InvalidOptionIterableLengthRangeError(
            option_name=option_name,
            minimum_elements=minimum_elements,
            maximum_elements=maximum_elements,
        )
