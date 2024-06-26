"""
Exception hierarchy for option configuration:

- BaseFrameworkException: Base class for all framework exceptions.
  - OptionValueValidationError: Error validating an option value.
  - RequiredOptionValueNotSetError: Required option value not set.
  - OptionConfigurationError: Error configuring an option.
    - InvalidValidatingRegexError:
    - EmptyOptionNameError:
    - InvalidDefaultValueError:
"""

from typing import Any

from consortium.server.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class OptionValueValidationError(BaseFrameworkException):
    def __init__(
        self,
        message: str,
    ):
        super().__init__(message)


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
    def __init__(
        self,
        message: str = "An error occurred while configuring the option.",
    ):
        super().__init__(message)


class OptionConfigurationParameterTypeError(OptionConfigurationError):
    def __init__(
        self,
        option_name: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            error_message = (
                f"Failed to configure option. The parameter '{parameter_name}' must be "
                f"of type '{parameter_type}' for option '{option_name}'."
            )
        super().__init__(error_message)


class InvalidValidatingRegexError(OptionConfigurationError):
    def __init__(
        self,
        option_name: str,
        validating_regex: str,
        regex_error_message: str,
    ):
        super().__init__(
            "Failed to configure option. The provided validating regex "
            f"'{validating_regex}' for option '{option_name}' is not valid. "
            f"{regex_error_message}",
        )


class EmptyOptionNameError(OptionConfigurationError):
    def __init__(self, option_name: str):
        super().__init__(
            f"Failed to configure option. The name for option '{option_name}' cannot "
            "be an empty string.",
        )


class InvalidDefaultValueError(OptionConfigurationError):
    def __init__(
        self,
        option_name: str,
        default_value: Any,
        error_message: str,
    ):
        super().__init__(
            f"The provided default value '{default_value}' for option '{option_name}' "
            f"is invalid. {error_message}",
        )


class EmptyAvailableValuesError(OptionConfigurationError):
    def __init__(self, option_name: str):
        super().__init__(
            f"Failed to configure option. The 'available_values' parameter for option "
            f"'{option_name}' cannot be an empty set.",
        )
