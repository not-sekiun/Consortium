from typing import Any

from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentConfigurationError,
    ComponentsFrameworkError,
    EmptyComponentLabelError,
    InvalidComponentConfigurationParameterTypeError,
    InvalidComponentDependencyVersionSpecifierError,
    InvalidComponentVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingComponentConfigurationParameterError,
)


class AgentTemplatesFrameworkError(
    ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the agent templates framework."""

    code = "AGENT_TEMPLATES_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "agent template"


class AgentTemplateConfigurationError(
    ComponentConfigurationError,
    AgentTemplatesFrameworkError,
):
    """Base exception for all errors that occur during the configuration of a particular
    agent template.
    """

    code = "AGENT_TEMPLATE_CONFIGURATION_ERROR"


class InvalidAgentTemplateConfigurationParameterTypeError(
    InvalidComponentConfigurationParameterTypeError,
    AgentTemplateConfigurationError,
):
    """Raised when an agent template's configuration parameter is not of the expected
    type during agent template configuration.
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
    MissingComponentConfigurationParameterError,
    AgentTemplateConfigurationError,
):
    """Raised when a required parameter is not declared in an agent template's definition
    during agent template configuration.
    """

    code = "MISSING_AGENT_TEMPLATE_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, agent_template_str: str, parameter_name: str):
        super().__init__(
            component_str=agent_template_str,
            parameter_name=parameter_name,
        )


class EmptyAgentTemplateLabelError(
    EmptyComponentLabelError,
    AgentTemplateConfigurationError,
):
    """Raised when an empty label is provided in an agent template's definition during
    agent template configuration.
    """

    code = "EMPTY_AGENT_TEMPLATE_LABEL_ERROR"

    def __init__(self, agent_template_filepath: str):
        super().__init__(component_filepath=agent_template_filepath)


class InvalidAgentTemplateVersionError(
    InvalidComponentVersionError,
    AgentTemplateConfigurationError,
):
    """Raised when the agent template version string provided in an agent template's
    definition is not a valid version string according to PEP 440 during agent template
    configuration.
    """

    code = "INVALID_AGENT_TEMPLATE_VERSION_ERROR"

    def __init__(self, agent_template_str: str, version: str):
        super().__init__(
            component_str=agent_template_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    InvalidFrameworkVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """Raised when the framework version specifier string provided in an agent template's
    definition is not a valid version specifier string as defined in PEP 440 during
    agent template configuration.
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
    InvalidComponentDependencyVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """Raised when an agent template dependency version specifier string provided in an
    agent template's definition is not a valid version specifier string as defined in
    PEP 440 during agent template configuration.
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
    """Raised when duplicate option names are provided in an agent template's definition
    during agent template configuration.
    """

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
    """Base exception for all errors related to agent template options."""

    code = "AGENT_TEMPLATE_OPTION_ERROR"


class AgentTemplateOptionNotFoundError(AgentTemplateOptionError):
    """Raised when a provided option name is not found in the agent template when
    attempting to create an agent generator from the agent template.
    """

    code = "AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR"

    def __init__(self, agent_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the agent generator from the agent template "
                f"'{agent_template_str}'. The provided option '{option_name}' was not "
                f"found in the agent template."
            ),
            detail={"option_str": option_name},
        )


class AgentTemplateOptionValueValidationError(AgentTemplateOptionError):
    """Raised when an invalid value is provided for an agent template option when
    attempting to create an agent generator from the agent template.
    """

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
                "option_str": option_name,
                "option_value": option_value,
                "error_message": error_message,
            },
        )


class MissingRequiredAgentTemplateOptionError(
    AgentTemplateOptionError,
):
    """Raised when a required option is not provided when attempting to create an agent
    generator from the agent template.
    """

    code = "MISSING_REQUIRED_AGENT_TEMPLATE_OPTION_ERROR"

    def __init__(self, agent_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the agent generator from the agent template "
                f"'{agent_template_str}'. The required option '{option_name}' was not "
                f"provided."
            ),
            detail={"option_str": option_name},
        )
