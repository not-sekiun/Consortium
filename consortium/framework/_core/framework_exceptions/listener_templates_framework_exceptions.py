from typing import Any

from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions,
)


class ListenerTemplatesFrameworkError(
    components_framework_exceptions.ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the listener templates framework."""

    code = "LISTENER_TEMPLATES_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "listener template"


class ListenerTemplateConfigurationError(
    components_framework_exceptions.ComponentConfigurationError,
    ListenerTemplatesFrameworkError,
):
    """Base exception for all errors that occur during the configuration of a particular
    listener template.
    """

    code = "LISTENER_TEMPLATE_CONFIGURATION_ERROR"


class InvalidListenerTemplateConfigurationParameterTypeError(
    components_framework_exceptions.InvalidComponentConfigurationParameterTypeError,
    ListenerTemplateConfigurationError,
):
    """Raised when a listener template's configuration parameter is not of the expected
    type during listener template configuration.
    """

    code = "INVALID_LISTENER_TEMPLATE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingListenerTemplateConfigurationParameterError(
    components_framework_exceptions.MissingComponentConfigurationParameterError,
    ListenerTemplateConfigurationError,
):
    """Raised when a required parameter is not declared in a listener template's definition
    during listener template configuration.
    """

    code = "MISSING_LISTENER_TEMPLATE_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, listener_template_str: str, parameter_name: str):
        super().__init__(
            component_str=listener_template_str,
            parameter_name=parameter_name,
        )


class EmptyListenerTemplateLabelError(
    components_framework_exceptions.EmptyComponentLabelError,
    ListenerTemplateConfigurationError,
):
    """Raised when an empty label is provided in a listener template's definition during
    listener template configuration.
    """

    code = "EMPTY_LISTENER_TEMPLATE_LABEL_ERROR"

    def __init__(self, listener_template_str_filepath: str):
        super().__init__(component_filepath=listener_template_str_filepath)


class InvalidListenerTemplateVersionError(
    components_framework_exceptions.InvalidComponentVersionError,
    ListenerTemplateConfigurationError,
):
    """Raised when the listener template version string provided in a listener template's
    definition is not a valid version string according to PEP 440 during listener template
    configuration.
    """

    code = "INVALID_LISTENER_TEMPLATE_VERSION_ERROR"

    def __init__(self, listener_template_str: str, version: str):
        super().__init__(
            component_str=listener_template_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    components_framework_exceptions.InvalidFrameworkVersionSpecifierError,
    ListenerTemplateConfigurationError,
):
    """Raised when the framework version specifier string provided in a listener template's
    definition is not a valid version specifier string as defined in PEP 440 during
    listener template configuration.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        framework_version_specifier: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            framework_version_specifier=framework_version_specifier,
        )


class InvalidListenerTemplateDependencyVersionSpecifierError(
    components_framework_exceptions.InvalidComponentDependencyVersionSpecifierError,
    ListenerTemplateConfigurationError,
):
    """Raised when a listener template dependency version specifier string provided in a
    listener template's definition is not a valid version specifier string as defined in
    PEP 440 during listener template configuration.
    """

    code = "INVALID_LISTENER_TEMPLATE_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=listener_template_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class DuplicateListenerTemplateOptionNameError(ListenerTemplateConfigurationError):
    """Raised when duplicate option names are provided in a listener template's definition
    during listener template configuration.
    """

    code = "DUPLICATE_LISTENER_TEMPLATE_OPTION_NAME_ERROR"

    def __init__(self, listener_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to configure the listener template {listener_template_str}'. "
                f"The options provided to the listener template must not have "
                f"duplicate names but the name '{option_name}' was duplicated."
            ),
        )


class ListenerTemplateOptionError(ListenerTemplatesFrameworkError):
    """Base exception for all errors related to listener template options."""

    code = "LISTENER_TEMPLATE_OPTION_ERROR"


class ListenerTemplateOptionNotFoundError(ListenerTemplateOptionError):
    """Raised when a provided option name is not found in the listener template when
    attempting to create a listener from the listener template.
    """

    code = "LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR"

    def __init__(self, listener_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the listener from the listener template "
                f"'{listener_template_str}'. The provided option '{option_name}' was not "
                f"found in the listener template."
            ),
        )


class ListenerTemplateOptionValueValidationError(ListenerTemplateOptionError):
    """Raised when an invalid value is provided for a listener template option when
    attempting to create a listener from the listener template.
    """

    code = "LISTENER_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR"

    def __init__(
        self,
        listener_template_str: str,
        option_name: str,
        option_value: Any,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to create the listener from the listener template "
                f"'{listener_template_str}'. The provided value '{option_value}' for "
                f"the option '{option_name}' is invalid. {error_message}"
            ),
            detail={
                "option_str": option_name,
                "option_value": option_value,
                "error_message": error_message,
            },
        )


class MissingRequiredListenerTemplateOptionError(
    ListenerTemplateOptionError,
):
    """Raised when a required option is not provided when attempting to create a listener
    from the listener template.
    """

    code = "MISSING_REQUIRED_LISTENER_TEMPLATE_OPTION_ERROR"

    def __init__(self, listener_template_str: str, option_name: str):
        super().__init__(
            message=(
                f"Failed to create the listener from the listener template "
                f"'{listener_template_str}'. The required option '{option_name}' was not "
                f"provided."
            ),
            detail={
                "listener_template_str": listener_template_str,
                "option_str": option_name,
            },
        )
