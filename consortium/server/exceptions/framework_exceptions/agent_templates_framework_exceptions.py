"""
Exception hierarchy for agent templates framework:

BaseFrameworkException: Base class for all framework exceptions.
- AgentTemplatesFrameworkError: General error occurred in the agent templates framework.
  - AgentTemplateConfigurationError: Error occurred during agent template configuration.
    - AgentTemplateConfigurationParameterError: Error with an agent template
    configuration parameter.
      - AgentTemplateConfigurationParameterTypeError: Invalid type for an agent
      template configuration parameter.
      - RequiredAgentTemplateConfigurationParameterNotDeclaredError: Required parameter
      not declared in agent template configuration.
    - EmptyAgentTemplateNameError: The name provided for an agent template is an
    empty string.
    - DuplicateAgentTemplateOptionNameError: Duplicate option name in agent template
    configuration.
  - AgentTemplateOptionError: Error related to an agent template option.
    - AgentTemplateOptionNotFoundError: Specified option not found in agent template.
    - AgentTemplateOptionValueError: Invalid value provided for an agent template
    option.
"""

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentTemplatesFrameworkError(BaseFrameworkException):
    pass


class AgentTemplateConfigurationError(AgentTemplatesFrameworkError):
    pass


class AgentTemplateConfigurationParameterError(AgentTemplateConfigurationError):
    pass


class AgentTemplateConfigurationParameterTypeError(
    AgentTemplateConfigurationParameterError,
):
    def __init__(
        self,
        agent_template: str | None = None,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the agent template '{agent_template}'. "
                    f"The parameter '{parameter_name}' must be of type "
                    f"'{parameter_type}' in the agent template's definition."
                ),
            )
        else:
            super().__init__(
                message=(
                    f"Failed to configure the agent template '{agent_template}'. "
                    f"{error_message}"
                ),
            )


class RequiredAgentTemplateConfigurationParameterNotDeclaredError(
    AgentTemplateConfigurationParameterError,
):
    def __init__(self, parameter_name: str, agent_template: str):
        super().__init__(
            message=(
                f"Failed to configure the agent template '{agent_template}'. "
                f"The required parameter '{parameter_name}' was not declared in the "
                f"agent template's definition."
            ),
        )


class EmptyAgentTemplateNameError(AgentTemplateConfigurationError):
    def __init__(self, agent_template_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the agent template defined at "
                f"'{agent_template_filepath}'. The name provided in the agent "
                f"template's definition during configuration cannot be empty."
            ),
        )


class DuplicateAgentTemplateOptionNameError(AgentTemplateConfigurationError):
    def __init__(self, option_name: str, agent_template: str):
        super().__init__(
            message=(
                f"Failed to configure the agent template {agent_template}'. The "
                f"options provided to the agent template must not have duplicate "
                f"names but the name '{option_name}' was duplicated."
            ),
        )


class AgentTemplateOptionError(AgentTemplatesFrameworkError):
    pass


class AgentTemplateOptionNotFoundError(AgentTemplateOptionError):
    def __init__(self, option_name: str, agent_template: str):
        super().__init__(
            message=(
                f"Failed to access the option '{option_name}' for the agent template "
                f"{agent_template}. Could not find the requested option "
                f"'{option_name}' in the agent template."
            ),
        )


class AgentTemplateOptionValueError(AgentTemplateOptionError):
    def __init__(
        self,
        agent_template: str,
        option_name: str,
        option_value: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to set the option '{option_name}' to the value "
                f"'{option_value}' for the agent template '{agent_template}'. "
                f"{error_message}"
            ),
        )
