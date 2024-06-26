"""
Exception hierarchy for listener template framework exceptions:

- BaseFrameworkException: Base class for all framework exceptions.
  - ListenerTemplateException: Base class for all listener template-related exceptions.
    - ListenerTemplateConfigurationError: Error configuring a listener template.
      - ListenerTemplateConfigurationParameterError: Error with a listener template
      parameter.
        - ListenerTemplateConfigurationParameterTypeError: Invalid type for listener
        template parameter.
        - RequiredListenerTemplateConfigurationParameterNotDeclaredError: Required
        parameter not declared for listener template.
      - InvalidListenerTemplateNameError: Error with the listener template name.
        - EmptyListenerTemplateNameError: Listener template name is empty.
      - DuplicateListenerTemplateOptionNameError: Duplicate option name in listener
      template.
    - ListenerTemplateOptionError: Error related to a listener template option.
      - ListenerTemplateOptionNotFoundError: Option with provided name not found in
      listener template.
      - ListenerTemplateOptionValueError: Provided value for listener template option
      is invalid.
"""

from consortium.server.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerTemplateException(BaseFrameworkException):
    def __init__(self, message: str = "An error occurred with the listener template."):
        super().__init__(message)


class ListenerTemplateConfigurationError(ListenerTemplateException):
    def __init__(
        self,
        message: str = "An error occurred while configuring the listener template.",
    ):
        super().__init__(message)


class ListenerTemplateConfigurationParameterError(ListenerTemplateConfigurationError):
    def __init__(
        self,
        message: str = (
            "An error occurred with a parameter while configuring the listener "
            "template."
        ),
    ):
        super().__init__(message)


class ListenerTemplateConfigurationParameterTypeError(
    ListenerTemplateConfigurationParameterError,
):
    def __init__(
        self,
        listener_template_name: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            error_message = (
                f"The parameter '{parameter_name}' must be of type '{parameter_type}' "
                f"for listener template '{listener_template_name}'."
            )
        super().__init__(
            f"Failed to configure the listener template. {error_message}",
        )


class RequiredListenerTemplateConfigurationParameterNotDeclaredError(
    ListenerTemplateConfigurationParameterError,
):
    def __init__(self, parameter_name: str, listener_template_name: str):
        super().__init__(
            "Failed to configure the listener template. The required parameter "
            f"'{parameter_name}' was not declared in listener template "
            f"'{listener_template_name}'.",
        )


class InvalidListenerTemplateNameError(ListenerTemplateConfigurationError):
    def __init__(
        self,
        message: str = "An error occurred with the listener template name.",
    ):
        super().__init__(message)


class EmptyListenerTemplateNameError(InvalidListenerTemplateNameError):
    def __init__(self):
        super().__init__(
            "Failed to configure the listener template. The listener template's name "
            "cannot be empty.",
        )


class DuplicateListenerTemplateOptionNameError(ListenerTemplateConfigurationError):
    def __init__(self, option_name: str, listener_template_name: str):
        super().__init__(
            f"The options provided to the listener template '{listener_template_name}' "
            f"must not have duplicated names. The name '{option_name}' was duplicated",
        )


class ListenerTemplateOptionError(ListenerTemplateException):
    def __init__(
        self,
        message: str = "An error occurred with an option for the listener template.",
    ):
        super().__init__(message)


class ListenerTemplateOptionNotFoundError(ListenerTemplateOptionError):
    def __init__(self, option_name: str, listener_template_name: str):
        super().__init__(
            "Failed to find the requested option. No option with the name "
            f"'{option_name}' was found in the listener template "
            f"'{listener_template_name}'.",
        )


class ListenerTemplateOptionValueError(ListenerTemplateOptionError):
    def __init__(
        self,
        listener_template_name: str,
        option_name: str,
        option_value: str,
        error_message: str,
    ):
        super().__init__(
            f"Failed to set the option '{option_name}' to the value '{option_value}' "
            f"for listener template '{listener_template_name}'. {error_message}",
        )
