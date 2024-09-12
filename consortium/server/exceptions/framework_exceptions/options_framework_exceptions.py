"""
Exception hierarchy for options framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - OptionValueValidationError: Error occurred while validating an option's value.
  - RequiredOptionValueNotSetError: A required option value was not set and has no
  default value.
  - OptionConfigurationError: Error occurred during option configuration.
    - OptionConfigurationParameterTypeError: Invalid type for an option configuration
    parameter.
    - InvalidValidatingRegexError: The regex provided for option validation is invalid.
    - EmptyOptionNameError: The name provided for an option is an empty string.
    - InvalidDefaultValueError: The default value provided for an option is invalid.
    - EmptyAvailableValuesError: The set of available values for an option is empty.
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class OptionValueValidationError(BaseFrameworkException):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message=message, detail=detail)


class RequiredOptionValueNotSetError(BaseFrameworkException):
    def __init__(
        self,
        option_name: str,
    ):
        super().__init__(
            f"Failed to retrieve the value of the required option '{option_name}'. "
            "No value has been set and no default value is present.",
        )


class OptionConfigurationError(BaseFrameworkException):
    pass


class OptionConfigurationParameterTypeError(OptionConfigurationError):
    def __init__(
        self,
        option_name: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure option '{option_name}'. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"option's. definition"
                ),
            )
        else:
            super().__init__(
                f"Failed to configure option '{option_name}'. {error_message}",
            )


class InvalidValidatingRegexError(OptionConfigurationError):
    def __init__(
        self,
        option_name: str,
        validating_regex: str,
        regex_error_message: str,
    ):
        super().__init__(
            f"Failed to configure option '{option_name}'. The provided validating "
            f"regex '{validating_regex}' in the option's definition during "
            f"configuration is not valid: {regex_error_message}",
        )


class EmptyOptionNameError(OptionConfigurationError):
    def __init__(self, option_filepath: str):
        super().__init__(
            f"Failed to configure the option defined at '{option_filepath}'. The name "
            f"provided in the option's parameters during creation cannot empty.",
        )


class InvalidDefaultValueError(OptionConfigurationError):
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


class EmptyAvailableValuesError(OptionConfigurationError):
    def __init__(self, option_name: str):
        super().__init__(
            f"Failed to configure option '{option_name}'. The 'available_values' "
            f"parameter for the option cannot be an empty set.",
        )
