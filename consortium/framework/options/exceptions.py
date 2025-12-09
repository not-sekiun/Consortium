"""
This module describes all the exceptions that can be raised by the options framework.
These exceptions are distinctly different from the "signalling" exceptions that are
present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
module. The exceptions here do not serve any message passing or signalling purpose to or
from the framework. Instead, they are raised when an error condition occurs and are also
meant to be used by the REST API layer.

The exception hierarchy for the options framework is as follows:

- [`BaseFrameworkException`][consortium.server.exceptions.framework_exceptions.base_framework_exception.BaseFrameworkException]
    - [`OptionsFrameworkError`][consortium.framework.options.exceptions.OptionsFrameworkError]
        - [`OptionValueValidationError`][consortium.framework.options.exceptions.OptionValueValidationError]
        - [`RequiredOptionValueNotSetError`][consortium.framework.options.exceptions.RequiredOptionValueNotSetError]
        - [`OptionConfigurationError`][consortium.framework.options.exceptions.OptionConfigurationError]
            - [`InvalidOptionConfigurationParameterTypeError`][consortium.framework.options.exceptions.InvalidOptionConfigurationParameterTypeError]
            - [`EmptyOptionNameError`][consortium.framework.options.exceptions.EmptyOptionNameError]
            - [`InvalidDefaultValueError`][consortium.framework.options.exceptions.InvalidDefaultValueError]
            - [`InvalidValidatingRegexError`][consortium.framework.options.exceptions.InvalidValidatingRegexError]
            - [`InvalidOptionValueLengthRangeError`][consortium.framework.options.exceptions.InvalidOptionValueLengthRangeError]
            - [`InvalidOptionValueLengthBoundError`][consortium.framework.options.exceptions.InvalidOptionValueLengthBoundError]
            - [`InvalidOptionValueRangeError`][consortium.framework.options.exceptions.InvalidOptionValueRangeError]
            - [`InvalidOptionIterableLengthRangeError`][consortium.framework.options.exceptions.InvalidOptionIterableLengthRangeError]
            - [`InvalidOptionIterableLengthBoundError`][consortium.framework.options.exceptions.InvalidOptionIterableLengthBoundError]
            - [`EmptyAvailableValuesError`][consortium.framework.options.exceptions.EmptyAvailableValuesError]
"""

from typing import Any, Literal

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class OptionsFrameworkError(BaseFrameworkException):
    """
    Base exception for all errors that occur within the options framework.
    """


class OptionValueValidationError(BaseFrameworkException):
    """
    An error that is raised when a provided value for an option fails any sort of
    data validation test. This error will primarily be raised when setting the value of
    an option through its `set_option_value()` method or when just explicitly validating
    the value of an option through its `validate_option_value()` method.
    """

    def __init__(self, message: str, detail: Any = None):
        super().__init__(message=message, detail=detail)


class RequiredOptionValueNotSetError(BaseFrameworkException):
    """
    An error that is raised when an option is marked as being required by setting its
    `required` parameter to `True`, but no value has been set for the option through
    its `set_option_value()` method and no default value has been provided for the
    option through its `default_value` parameter.
    """

    def __init__(
        self,
        option_name: str,
    ):
        super().__init__(
            f"Failed to retrieve the value of the required option '{option_name}'. "
            "No value has been set and no default value is present.",
        )


class OptionConfigurationError(BaseFrameworkException):
    """
    Base exception for all errors that occur during the configuration of a particular
    option.
    """


class InvalidOptionConfigurationParameterTypeError(OptionConfigurationError):
    """
    An error that is raised when the argument that is passed to configure an option is
    not of the expected type for that particular parameter. All option types can raise
    this error
    """

    def __init__(
        self,
        option_name: str,
        parameter_name: str | None = None,
        expected_parameter_type_string: str | None = None,
        actual_parameter_type_string: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the option '{option_name}'. The parameter "
                    f"'{parameter_name}' passed to the option must be of type "
                    f"'{expected_parameter_type_string}' but was of type "
                    f"'{actual_parameter_type_string}'."
                ),
            )
        else:
            super().__init__(
                f"Failed to configure the option '{option_name}'. {error_message}",
            )


class EmptyOptionNameError(OptionConfigurationError):
    """
    An error that is raised when the name provided for an option during its creation is
    an empty string. All option types can raise this error.
    """

    def __init__(self, option_filepath: str):
        super().__init__(
            f"Failed to configure the option defined at '{option_filepath}'. The name "
            f"provided in the option's parameters during creation cannot empty.",
        )


class InvalidDefaultValueError(OptionConfigurationError):
    """
    An error that is raised when the invalid default value provided to an option through
    its `default_value` parameter fails data validation through its `validate_value()`
    method. All option types can raise this error.
    """

    def __init__(
        self,
        option_name: str,
        default_value: Any,
        option_value_validation_error_message: str,
    ):
        super().__init__(
            f"Failed to configure the option '{option_name}'. The provided default "
            f"value '{default_value}' for the option is invalid: "
            f"{option_value_validation_error_message}",
        )


class InvalidValidatingRegexError(OptionConfigurationError):
    """
    An error that is raised when the `validating_regex` regex string provided for
    validating an option's value is not a valid regex that can be compiled. Only options
    of type `SingleValueOption`, `ListValueOption`, and `DictionaryValueOption` can
    raise this error.
    """

    def __init__(
        self,
        option_name: str,
        validating_regex: str,
        regex_error_message: str,
    ):
        super().__init__(
            f"Failed to configure the option '{option_name}'. The provided validating "
            f"regex '{validating_regex}' in the option's definition during "
            f"configuration is not valid: {regex_error_message}",
        )


class InvalidOptionValueLengthRangeError(OptionConfigurationError):
    """
    An error that is raised when the `minimum_length` parameter provided for an option
    is greater than the `maximum_length` parameter leading to an invalid range of
    values for the string value. Only options of type `SingleValueOption`,
    `ListValueOption`, or `DictionaryValueOption` can raise this error. Additionally,
    the value type of the options must be of type `str`.
    """

    def __init__(
        self,
        option_name: str,
        minimum_length: int,
        maximum_length: int,
    ):
        super().__init__(
            f"Failed to configure option '{option_name}'. The `minimum_length` "
            f"parameter '{minimum_length}' cannot be greater than the `maximum_length` "
            f"parameter '{maximum_length}'.",
        )


class InvalidOptionValueLengthBoundError(OptionConfigurationError):
    """
    An error that is raised when the `minimum_length` or `maximum_length` parameter
    provided for an option specifying the length of the string value is less than zero.
    Only options of type `SingleValueOption`, `ListValueOption`, or
    `DictionaryValueOption` can raise this error. Additionally, the value type of the
    options must be of type `str`.
    """

    def __init__(
        self,
        option_name: str,
        length_bound_parameter_name: Literal["minimum_length", "maximum_length"],
        length_bound: int,
    ):
        super().__init__(
            f"Failed to configure option '{option_name}'. The "
            f"`{length_bound_parameter_name}` parameter '{length_bound}' must be "
            f"greater than or equal to zero.",
        )


class InvalidOptionValueRangeError(OptionConfigurationError):
    """
    An error that is raised when the `lesser_than` or `lesser_than_or_equal_to`
    parameter provided for an option is greater than the `greater_than` or
    `greater_than_or_equal_to` parameter leading to an invalid range of numeric values
    that the option can take. Only options of type `SingleValueOption`,
    `ListValueOption`, or `DictionaryValueOption` can raise this error. Additionally,
    the value type of the options must be of type `int` or `float`.
    """

    def __init__(
        self,
        option_name: str,
        minimum_range_parameter_name: Literal["lesser_than", "lesser_than_or_equal_to"],
        maximum_range_parameter_name: Literal[
            "greater_than",
            "greater_than_or_equal_to",
        ],
        minimum_range: int,
        maximum_range: int,
    ):
        # `greater_than` parameter cannot be greater than the `lesser_than` parameter.
        if (
            minimum_range_parameter_name == "lesser_than"
            and maximum_range_parameter_name == "greater_than"
        ):
            erroneous_comparison_type = "greater than"
        # `greater_than_or_equal_to` parameter cannot be greater than or equal to the
        # `lesser_than` parameter.
        elif (
            minimum_range_parameter_name == "lesser_than"
            and maximum_range_parameter_name == "greater_than_or_equal_to"
        ):
            erroneous_comparison_type = "greater than or equal to"
        # `greater_than` parameter cannot be greater than or equal to the
        # `lesser_than_or_equal_to` parameter.
        elif (
            minimum_range_parameter_name == "lesser_than_or_equal_to"
            and maximum_range_parameter_name == "greater_than"
        ):
            erroneous_comparison_type = "greater than"
        # `greater_than_or_equal_to` parameter cannot be greater than the
        # `lesser_than_or_equal_to` parameter.
        elif (
            minimum_range_parameter_name == "lesser_than_or_equal_to"
            and maximum_range_parameter_name == "greater_than_or_equal_to"
        ):
            erroneous_comparison_type = "greater than or equal to"
        else:
            raise AssertionError(
                "The provided values for the minimum range parameter name "
                f"'{minimum_range_parameter_name}' and maximum range parameter name "
                f"'{maximum_range_parameter_name}' are invalid."
            )

        super().__init__(
            f"Failed to configure option '{option_name}'. The "
            f"`{minimum_range_parameter_name}` parameter '{minimum_range}' cannot be "
            f"{erroneous_comparison_type} the `{maximum_range_parameter_name}` "
            f"parameter '{maximum_range}'.",
        )


class InvalidOptionIterableLengthRangeError(OptionConfigurationError):
    """
    An error that is raised when the `minimum_elements` parameter provided for an option
    is greater than the `maximum_elements` parameter leading to an invalid range of
    elements for the iterable value. Only options of type `ListValueOption`, or
    `DictionaryValueOption` can raise this error.
    """

    def __init__(
        self,
        option_name: str,
        minimum_elements: int,
        maximum_elements: int,
    ):
        super().__init__(
            f"Failed to configure option '{option_name}'. The `minimum_elements` "
            f"parameter '{minimum_elements}' cannot be greater than the "
            f"`maximum_elements` parameter '{maximum_elements}'.",
        )


class InvalidOptionIterableLengthBoundError(OptionConfigurationError):
    """
    An error that is raised when the `minimum_elements` or `maximum_elements` parameter
    provided for an option specifying the length of the string value is less than zero.
    Only options of type `ListValueOption`, or `DictionaryValueOption` can raise this error.
    """

    def __init__(
        self,
        option_name: str,
        length_bound_parameter_name: Literal["minimum_elements", "maximum_elements"],
        length_bound: int,
    ):
        super().__init__(
            f"Failed to configure option '{option_name}'. The "
            f"`{length_bound_parameter_name}` parameter '{length_bound}' must be "
            f"greater than or equal to zero.",
        )


class EmptyAvailableValuesError(OptionConfigurationError):
    """
    An error that is raised when the set of available values that an option can take
    through its `available_values` parameter is empty. Only options of type
    `ChoiceValueOption` can raise this error.
    """

    def __init__(self, option_name: str):
        super().__init__(
            f"Failed to configure the option '{option_name}'. The 'available_values' "
            f"parameter for the option cannot be an empty set.",
        )
