"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`AgentTemplatesError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplatesError]
        - [`AgentTemplatesFrameworkError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplatesFrameworkError]
            - [`AgentTemplateConfigurationError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateConfigurationError]
                - [`InvalidAgentTemplateConfigurationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.InvalidAgentTemplateConfigurationParameterTypeError]
                - [`MissingAgentTemplateConfigurationParameterError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.MissingAgentTemplateConfigurationParameterError]
                - [`EmptyAgentTemplateLabelError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.EmptyAgentTemplateLabelError]
                - [`InvalidAgentTemplateVersionError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.InvalidAgentTemplateVersionError]
                - [`InvalidFrameworkVersionSpecifierError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.InvalidFrameworkVersionSpecifierError]
                - [`InvalidAgentTemplateDependencyVersionSpecifierError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.InvalidAgentTemplateDependencyVersionSpecifierError]
                - [`DuplicateAgentTemplateOptionNameError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.DuplicateAgentTemplateOptionNameError]
            - [`AgentTemplateOptionError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateOptionError]
                - [`AgentTemplateOptionNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateOptionNotFoundError]
                - [`AgentTemplateOptionValueValidationError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateOptionValueValidationError]
                - [`MissingRequiredAgentTemplateOptionError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.MissingRequiredAgentTemplateOptionError]
        - [`AgentTemplatesServiceError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplatesServiceError]
            - [`AgentTemplateNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateNotFoundError]
                - [`AgentTemplateIDNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateIDNotFoundError]
                - [`AgentTemplateLabelNotFoundError`][consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions.AgentTemplateLabelNotFoundError]
"""
# TODO: The docstring generator tool for some reason missed out on InvalidFrameworkVersionSpecifierError agent template, listener template, event hooks and plugins exceptions

from typing import Any

from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class AgentTemplatesError(BaseConsortiumError):
    """
    Base exception for all agent templates-related errors.
    """

    code = "AGENT_TEMPLATES_ERROR"


class AgentTemplatesFrameworkError(AgentTemplatesError):
    """
    Base exception for all errors that occur within the agent templates framework.
    """

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
    Raised when an agent template's configuration parameter is not of the expected
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
    comp_excs.MissingComponentConfigurationParameterError,
    AgentTemplateConfigurationError,
):
    """
    Raised when a required parameter is not declared in an agent template's definition
    during agent template configuration.
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
    Raised when an empty label is provided in an agent template's definition during
    agent template configuration.
    """

    code = "EMPTY_AGENT_TEMPLATE_LABEL_ERROR"

    def __init__(self, agent_template_filepath: str):
        super().__init__(component_filepath=agent_template_filepath)


class InvalidAgentTemplateVersionError(
    comp_excs.InvalidComponentVersionError,
    AgentTemplateConfigurationError,
):
    """
    Raised when the agent template version string provided in an agent template's
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
    comp_excs.InvalidFrameworkVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """
    Raised when the framework version specifier string provided in an agent template's
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
    comp_excs.InvalidComponentDependencyVersionSpecifierError,
    AgentTemplateConfigurationError,
):
    """
    Raised when an agent template dependency version specifier string provided in an
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
    """
    Raised when duplicate option names are provided in an agent template's definition
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
    """
    Base exception for all errors related to agent template options.
    """

    code = "AGENT_TEMPLATE_OPTION_ERROR"


class AgentTemplateOptionNotFoundError(AgentTemplateOptionError):
    """
    Raised when a provided option name is not found in the agent template when
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
    """
    Raised when an invalid value is provided for an agent template option when
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
    """
    Raised when a required option is not provided when attempting to create an agent
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


class AgentTemplatesServiceError(AgentTemplatesError):
    """
    Base exception for all errors that occur within the agent templates service.
    """

    code = "AGENT_TEMPLATES_SERVICE_ERROR"


class AgentTemplateNotFoundError(AgentTemplatesServiceError):
    """
    Raised when the requested agent template was not found in the agent templates
    service.
    """

    code = "AGENT_TEMPLATE_NOT_FOUND_ERROR"


class AgentTemplateIDNotFoundError(AgentTemplateNotFoundError):
    """
    Raised when the requested agent template with the provided agent template ID was
    not found in the agent templates service.
    """

    code = "AGENT_TEMPLATE_ID_NOT_FOUND_ERROR"

    def __init__(self, agent_template_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent template. No agent template was "
                f"found with the provided agent template ID '{agent_template_id}'."
            ),
            detail={"agent_template_id": agent_template_id},
        )


class AgentTemplateLabelNotFoundError(AgentTemplateNotFoundError):
    """
    Raised when the requested agent template with the provided label was not found in
    the agent templates service.
    """

    code = "AGENT_TEMPLATE_LABEL_NOT_FOUND_ERROR"

    def __init__(self, label: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent template. No agent template was "
                f"found with the provided label '{label}'."
            ),
            detail={"label": label},
        )
