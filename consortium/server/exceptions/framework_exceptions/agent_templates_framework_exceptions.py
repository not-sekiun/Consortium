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

from typing import Any

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class AgentTemplatesFrameworkError(BaseFrameworkException):
    code = "AGENT_TEMPLATES_FRAMEWORK_ERROR"


class AgentTemplateConfigurationError(
    comp_excs.ComponentConfigurationError,
    AgentTemplatesFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    agent template.
    """

    code = "AGENT_TEMPLATE_CONFIGURATION_ERROR"

    _COMPONENT_TYPE = "agent template"


class InvalidAgentTemplateConfigurationParameterTypeError(
    comp_excs.InvalidComponentConfigurationParameterTypeError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when an agent template's configuration parameter is of an invalid
    type.
    """

    code = "INVALID_AGENT_TEMPLATE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_template_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=agent_template_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingAgentTemplateConfigurationParameterError(
    comp_excs.MissingComponentConfigurationParameterError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when a parameter is not declared in an agent template's definition.
    """

    code = "MISSING_AGENT_TEMPLATE_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, agent_template_str: str, parameter_name: str):
        super().__init__(
            component_str=agent_template_str,
            parameter_name=parameter_name,
        )


class EmptyAgentTemplateLabelError(
    comp_excs.EmptyComponentLabelError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when the label provided in an agent template's definition during
    configuration is an empty string.
    """

    code = "EMPTY_AGENT_TEMPLATE_LABEL_ERROR"

    def __init__(self, agent_template_filepath: str):
        super().__init__(component_filepath=agent_template_filepath)


class DuplicateAgentTemplateLabelError(
    comp_excs.DuplicateComponentLabelError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when the label provided in the agent template's definition during
    configuration is already in use by another agent template.
    """

    code = "DUPLICATE_AGENT_TEMPLATE_LABEL_ERROR"

    def __init__(self, agent_template_str: str, label: str):
        super().__init__(
            component_str=agent_template_str,
            label=label,
        )


class InvalidAgentTemplateVersionError(
    comp_excs.InvalidComponentVersionError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when the agent template version string provided in the agent template's
    definition during configuration is not a valid version string according to PEP 440.
    """

    code = "INVALID_AGENT_TEMPLATE_VERSION_ERROR"

    def __init__(self, agent_template_str: str, version: str):
        super().__init__(
            component_str=agent_template_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    comp_excs.InvalidFrameworkVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when the framework version specifier string provided in the
    agent template's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        agent_template_str: str,
        framework_version_specifier: str,
    ):
        super().__init__(
            component_str=agent_template_str,
            framework_version_specifier=framework_version_specifier,
        )


class InvalidAgentTemplateDependencyVersionSpecifierError(
    comp_excs.InvalidComponentDependencyVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """
    An error that is raised when the agent template dependency version specifier string
    provided in the agent template's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    code = "INVALID_AGENT_TEMPLATE_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        agent_template_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=agent_template_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class DuplicateAgentTemplateOptionNameError(AgentTemplateConfigurationError):
    code = "DUPLICATE_AGENT_TEMPLATE_OPTION_NAME_ERROR"

    def __init__(self, agent_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to configure the agent template {agent_template_str}'. "
                f"The options provided to the agent template must not have "
                f"duplicate names but the name '{option_name}' was duplicated."
            ),
        )


class AgentTemplateOptionError(AgentTemplatesFrameworkError):
    code = "AGENT_TEMPLATE_OPTION_ERROR"


class AgentTemplateOptionNotFoundError(AgentTemplateOptionError):
    code = "AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR"

    def __init__(self, agent_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the agent generator from the agent template "
                f"'{agent_template_str}'. The provided option '{option_name}' was not "
                f"found in the agent template."
            ),
            detail={"option_name": option_name},
        )


class AgentTemplateOptionValueValidationError(AgentTemplateOptionError):
    code = "AGENT_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR"

    def __init__(
        self,
        agent_template_str: str,
        option_name: str,
        option_value: Any,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to create the agent generator from the agent template "
                f"'{agent_template_str}'. The provided value '{option_value}' for the "
                f"option '{option_name}' is invalid. {error_message}"
            ),
            detail={
                "option_name": option_name,
                "option_value": option_value,
                "error_message": error_message,
            },
        )


class MissingRequiredAgentTemplateOptionError(
    AgentTemplateOptionError,
):
    code = "MISSING_REQUIRED_AGENT_TEMPLATE_OPTION_ERROR"

    def __init__(self, agent_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the agent generator from the agent template "
                f"'{agent_template_str}'. The required option '{option_name}' was not "
                f"provided."
            ),
            detail={"option_name": option_name},
        )
