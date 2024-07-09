"""
Exception hierarchy for listener template framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - ListenerTemplatesFrameworkException: General error occurred in the listener
  templates framework.
    - ListenerTemplateConfigurationError: Error during listener template configuration.
      - ListenerTemplateConfigurationParameterError: Error with a listener template
      parameter.
        - ListenerTemplateConfigurationParameterTypeError: Invalid type for a listener
        template parameter.
        - RequiredListenerTemplateConfigurationParameterNotDeclaredError: Required
        parameter not declared in listener template.
      - EmptyListenerTemplateNameError: Listener template name is an empty string.
      - DuplicateListenerTemplateOptionNameError: Duplicate option name in listener
      template configuration.
    - ListenerTemplateOptionError: Error related to a listener template option.
      - ListenerTemplateOptionNotFoundError: Specified option not found in listener
      template.
      - ListenerTemplateOptionValueError: Invalid value provided for a listener
      template option.
"""

from consortium.framework.exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenerTemplatesFrameworkError(BaseFrameworkException):
    pass


class ListenerTemplateConfigurationError(ListenerTemplatesFrameworkError):
    pass


class ListenerTemplateConfigurationParameterError(ListenerTemplateConfigurationError):
    pass


class ListenerTemplateConfigurationParameterTypeError(
    ListenerTemplateConfigurationParameterError,
):
    def __init__(
        self,
        listener_template_str: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the listener template "
                    f"'{listener_template_str}'. The parameter '{parameter_name}' "
                    f"must be of type '{parameter_type}' in the listener template's "
                    f"definition."
                )
            )
        else:
            super().__init__(
                message=(
                    f"Failed to configure the listener template "
                    f"'{listener_template_str}'. {error_message}"
                )
            )


class RequiredListenerTemplateConfigurationParameterNotDeclaredError(
    ListenerTemplateConfigurationParameterError,
):
    def __init__(self, parameter_name: str, listener_template_str: str):
        super().__init__(
            message=(
                f"Failed to configure the listener template "
                f"'{listener_template_str}'. The required parameter "
                f"'{parameter_name}' was not declared in the listener template's "
                f"definition."
            )
        )


class EmptyListenerTemplateNameError(ListenerTemplateConfigurationError):
    def __init__(self, listener_template_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the listener template defined at "
                f"'{listener_template_filepath}'. The name provided in the listener "
                f"template's definition during configuration cannot be empty."
            )
        )


class DuplicateListenerTemplateOptionNameError(ListenerTemplateConfigurationError):
    def __init__(self, option_name: str, listener_template_str: str):
        super().__init__(
            message=(
                f"Failed to configure the listener template {listener_template_str}'. "
                f"The options provided to the listener template must not have "
                f"duplicate names but the name '{option_name}' was duplicated."
            )
        )


class ListenerTemplateOptionError(ListenerTemplatesFrameworkError):
    pass


class ListenerTemplateOptionNotFoundError(ListenerTemplateOptionError):
    def __init__(self, option_name: str, listener_template_str: str):
        super().__init__(
            message=(
                f"Failed to access the option '{option_name}' for the listener "
                f"template {listener_template_str}. Could not find the requested "
                f"option '{option_name}' in the agent template."
            )
        )


class ListenerTemplateOptionValueError(ListenerTemplateOptionError):
    def __init__(
        self,
        listener_template_str: str,
        option_name: str,
        option_value: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to set the option '{option_name}' to the value "
                f"'{option_value}' for the listener template "
                f"'{listener_template_str}'. {error_message}"
            )
        )
