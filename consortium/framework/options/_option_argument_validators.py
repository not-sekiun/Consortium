import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Literal, Type

from consortium.framework.options.exceptions import (
    InvalidOptionConfigurationParameterTypeError,
    InvalidOptionIterableLengthBoundError,
    InvalidOptionIterableLengthRangeError,
    InvalidOptionValueLengthBoundError,
    InvalidOptionValueLengthRangeError,
    InvalidOptionValueRangeError,
    InvalidValidatingRegexError,
)

SimpleType = str | int | float | bool


@dataclass
class ArgumentDataTypeCheckParameters:
    value: Any
    expected_data_type: Type | set[Type]
    # If an error message is provided we will use that error message instead of
    # attempting to construct a default error message.
    error_message: str | None = None


# The following function is used to validate the data types of the arguments provided
# to the option configuration functions. This function also accounts for when those
# arguments are implicitly not provided, whereby they will be of type `None`.
def validate_arguments_data_types(
    option_name: str,
    *argument_data_type_check_parameters: ArgumentDataTypeCheckParameters,
):
    for parameter in argument_data_type_check_parameters:
        if parameter.value is None:
            continue
        if isinstance(parameter.expected_data_type, set):
            if parameter.error_message is None:
                parameter.error_message = (
                    f"The parameter '{parameter.value}' must be one of the types "
                    f"{", ".join([f"`{data_type}`" for data_type in parameter.expected_data_type])} "
                    f"for option '{option_name}'."
                )
            if not isinstance(parameter.value, tuple(parameter.expected_data_type)):
                raise InvalidOptionConfigurationParameterTypeError(
                    option_name=option_name,
                    error_message=parameter.error_message,
                )
        elif isinstance(parameter.expected_data_type, type):
            if not isinstance(parameter.value, parameter.expected_data_type):
                raise InvalidOptionConfigurationParameterTypeError(
                    option_name=option_name,
                    error_message=parameter.error_message,
                )
        else:
            assert False, (
                f"Invalid data type '{parameter.expected_data_type}' provided for "
                "`expected_data_type`."
            )


def validate_value_type_argument(
    option_name: str,
    value_type: Type[SimpleType],
) -> None:
    if value_type is not None and value_type not in {str, int, float, bool}:
        raise InvalidOptionConfigurationParameterTypeError(
            option_name=option_name,
            error_message=(
                f"The `value_type` parameter '{value_type}' must be of type `str`, "
                f"`int`, `float`, or `bool` for option '{option_name}'."
            ),
        )


def validate_string_length_arguments(
    option_name: str,
    option_value_type: Type,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    validate_arguments_data_types(
        option_name,
        ArgumentDataTypeCheckParameters(
            value=minimum_length,
            expected_data_type=int,
        ),
        ArgumentDataTypeCheckParameters(
            value=maximum_length,
            expected_data_type=int,
        ),
    )
    if minimum_length is not None or maximum_length is not None:
        if not issubclass(option_value_type, str):
            raise InvalidOptionConfigurationParameterTypeError(
                option_name=option_name,
                error_message=(
                    f"The parameters `minimum_length` and `maximum_length` are only "
                    f"applicable to options with a value type of `str`."
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
    option_value_type: Type,
    greater_than: int,
    lesser_than: int,
    greater_than_or_equal_to: int,
    lesser_than_or_equal_to: int,
) -> None:
    validate_arguments_data_types(
        option_name,
        ArgumentDataTypeCheckParameters(
            value=greater_than,
            expected_data_type=int,
        ),
        ArgumentDataTypeCheckParameters(
            value=lesser_than,
            expected_data_type=int,
        ),
        ArgumentDataTypeCheckParameters(
            value=greater_than_or_equal_to,
            expected_data_type=int,
        ),
        ArgumentDataTypeCheckParameters(
            value=lesser_than_or_equal_to,
            expected_data_type=int,
        ),
    )
    if any(
        (
            greater_than,
            lesser_than,
            greater_than_or_equal_to,
            lesser_than_or_equal_to,
        ),
    ):
        if not issubclass(option_value_type, (int, float)):
            raise InvalidOptionConfigurationParameterTypeError(
                error_message=(
                    f"Failed to configure option '{option_name}'. The parameters "
                    f"`greater_than`, `lesser_than`, `greater_than_or_equal_to`, and "
                    f"`lesser_than_or_equal_to` are only applicable to options with a "
                    f"value type of `int` or `float`."
                ),
            )
        if greater_than is not None:
            if lesser_than is not None and greater_than > lesser_than:
                raise InvalidOptionValueRangeError(
                    option_name=option_name,
                    minimum_range_parameter_name="lesser_than",
                    maximum_range_parameter_name="greater_than",
                    minimum_range=lesser_than,
                    maximum_range=greater_than,
                )
            if (
                lesser_than_or_equal_to is not None
                and greater_than > lesser_than_or_equal_to
            ):
                raise InvalidOptionValueRangeError(
                    option_name=option_name,
                    minimum_range_parameter_name="lesser_than_or_equal_to",
                    maximum_range_parameter_name="greater_than",
                    minimum_range=lesser_than_or_equal_to,
                    maximum_range=greater_than,
                )
        if greater_than_or_equal_to:
            if lesser_than is not None and greater_than_or_equal_to > lesser_than:
                raise InvalidOptionValueRangeError(
                    option_name=option_name,
                    minimum_range_parameter_name="lesser_than_or_equal_to",
                    maximum_range_parameter_name="greater_than_or_equal_to",
                    minimum_range=lesser_than_or_equal_to,
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
    if validating_regex:
        if not isinstance(validating_regex, str):
            raise InvalidOptionConfigurationParameterTypeError(
                parameter_name=validating_regex_parameter_name,
                expected_parameter_type_string="str",
                option_name=option_name,
            )
        try:
            re.compile(validating_regex)
        except re.error as exc:
            raise InvalidValidatingRegexError(
                option_name=option_name,
                validating_regex=validating_regex,
                regex_error_message=str(exc),
            )


def validate_validating_function_argument(
    option_name: str,
    validating_function: Callable[[Any], None] | None,
    validating_function_parameter_name: Literal[
        "validating_function",
        "key_validating_function",
        "value_validating_function",
    ] = "validating_function",
) -> None:
    if validating_function:
        if not isinstance(validating_function, Callable):
            raise InvalidOptionConfigurationParameterTypeError(
                option_name=option_name,
                parameter_name=validating_function_parameter_name,
                expected_parameter_type_string="callable",
            )
        function_signature = inspect.signature(validating_function)
        if len(function_signature.parameters) != 1:
            raise InvalidOptionConfigurationParameterTypeError(
                option_name=option_name,
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
    validate_arguments_data_types(
        option_name,
        ArgumentDataTypeCheckParameters(
            value=minimum_elements,
            expected_data_type=int,
        ),
        ArgumentDataTypeCheckParameters(
            value=maximum_elements,
            expected_data_type=int,
        ),
    )
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
