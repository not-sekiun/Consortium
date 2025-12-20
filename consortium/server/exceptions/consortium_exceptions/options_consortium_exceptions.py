"""
Exception hierarchy for options errors:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`OptionsError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.OptionsError]
        - [`OptionsFrameworkError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.OptionsFrameworkError]
            - [`OptionValueValidationError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.OptionValueValidationError]
            - [`OptionConfigurationError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.OptionConfigurationError]
                - [`InvalidOptionConfigurationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionConfigurationParameterTypeError]
                - [`EmptyOptionNameError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.EmptyOptionNameError]
                - [`InvalidDefaultValueError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidDefaultValueError]
                - [`InvalidValidatingRegexError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidValidatingRegexError]
                - [`InvalidOptionValueLengthRangeError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionValueLengthRangeError]
                - [`InvalidOptionValueLengthBoundError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionValueLengthBoundError]
                - [`InvalidOptionValueRangeError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionValueRangeError]
                - [`InvalidOptionIterableLengthRangeError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionIterableLengthRangeError]
                - [`InvalidOptionIterableLengthBoundError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.InvalidOptionIterableLengthBoundError]
                - [`EmptyAvailableValuesError`][consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions.EmptyAvailableValuesError]
"""

from typing import Any, Literal

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class OptionsError(BaseConsortiumError):
    """
    Base exception for all options-related errors.
    """


class OptionsFrameworkError(OptionsError):
    """
    Base exception for all errors that occur within the options framework.
    """


class OptionValueValidationError(OptionsFrameworkError):
    """
    Raised when a provided value for an option fails data validation when setting the
    value through the option's `set_option_value()` method or when explicitly validating
    the value through the option's `validate_option_value()` method.
    """

    def __init__(self, message: str, detail: Any = None):
        super().__init__(message=message, detail=detail)


class OptionConfigurationError(OptionsFrameworkError):
    """
    Base exception for all errors that occur during the configuration of a particular
    option.
    """


class InvalidOptionConfigurationParameterTypeError(OptionConfigurationError):
    """
    Raised when a parameter provided to configure an option is not of the expected type
    during option configuration.
    """

    def __init__(
        self,
        option_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str | None = None,
    ):
        if error_message is None:
            super().__init__(
                message=(
                    f"Failed to configure the option '{option_str}'. The parameter "
                    f"'{parameter_name}' passed to the option must be of type "
                    f"'{parameter_type}'."
                ),
            )
        else:
            super().__init__(
                f"Failed to configure the option '{option_str}'. {error_message}",
            )


class EmptyOptionNameError(OptionConfigurationError):
    """
    Raised when an empty name is provided for an option during option configuration.
    """

    def __init__(self, option_filepath: str):
        super().__init__(
            f"Failed to configure the option defined at '{option_filepath}'. The name "
            f"provided in the option's parameters during creation cannot empty.",
        )


class InvalidDefaultValueError(OptionConfigurationError):
    """
    Raised when the default value provided to an option through its `default_value`
    parameter fails data validation through the option's `validate_value()` method
    during option configuration.
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
    Raised when the `validating_regex` regex string provided for validating an option's
    value is not a valid regex pattern that can be compiled during option configuration.
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
    Raised when the `minimum_length` parameter provided for an option is greater than
    the `maximum_length` parameter, resulting in an invalid range of string value
    lengths during option configuration.
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
    Raised when the `minimum_length` or `maximum_length` parameter provided for an
    option specifying the length of the string value is less than zero during option
    configuration.
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
    Raised when the `less_than` or `less_than_or_equal_to` parameter provided for an
    option is greater than the `greater_than` or `greater_than_or_equal_to` parameter,
    resulting in an invalid range of numeric values during option configuration.
    """

    def __init__(
        self,
        option_name: str,
        minimum_range_parameter_name: Literal["less_than", "less_than_or_equal_to"],
        maximum_range_parameter_name: Literal[
            "greater_than",
            "greater_than_or_equal_to",
        ],
        minimum_range: int,
        maximum_range: int,
    ):
        # `greater_than` parameter cannot be greater than the `less_than` parameter.
        if (
            minimum_range_parameter_name == "less_than"
            and maximum_range_parameter_name == "greater_than"
        ):
            erroneous_comparison_type = "greater than"
        # `greater_than_or_equal_to` parameter cannot be greater than or equal to the
        # `less_than` parameter.
        elif (
            minimum_range_parameter_name == "less_than"
            and maximum_range_parameter_name == "greater_than_or_equal_to"
        ):
            erroneous_comparison_type = "greater than or equal to"
        # `greater_than` parameter cannot be greater than or equal to the
        # `less_than_or_equal_to` parameter.
        elif (
            minimum_range_parameter_name == "less_than_or_equal_to"
            and maximum_range_parameter_name == "greater_than"
        ):
            erroneous_comparison_type = "greater than"
        # `greater_than_or_equal_to` parameter cannot be greater than the
        # `less_than_or_equal_to` parameter.
        elif (
            minimum_range_parameter_name == "less_than_or_equal_to"
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
    Raised when the `minimum_elements` parameter provided for an option is greater than
    the `maximum_elements` parameter, resulting in an invalid range of iterable element
    counts during option configuration.
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
    Raised when the `minimum_elements` or `maximum_elements` parameter provided for an
    option specifying the number of elements in the iterable value is less than zero
    during option configuration.
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
    Raised when the set of available values provided through the `available_values`
    parameter is empty during option configuration.
    """

    def __init__(self, option_name: str):
        super().__init__(
            f"Failed to configure the option '{option_name}'. The `available_values` "
            f"parameter for the option cannot be an empty set.",
        )
