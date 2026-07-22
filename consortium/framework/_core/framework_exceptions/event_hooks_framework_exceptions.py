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


class EventHooksFrameworkError(
    ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the event hooks framework."""

    code = "EVENT_HOOKS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "event hook"


class EventHookConfigurationError(
    ComponentConfigurationError,
    EventHooksFrameworkError,
):
    """Base exception for all errors that occur during the configuration of a particular
    event hook.
    """

    code = "EVENT_HOOK_CONFIGURATION_ERROR"


class InvalidEventHookConfigurationParameterTypeError(
    InvalidComponentConfigurationParameterTypeError,
    EventHookConfigurationError,
):
    """Raised when an event hook's configuration parameter is not of the expected type during
    event hook configuration.
    """

    code = "INVALID_EVENT_HOOK_CONFIGURATION_PARAMETER_TYPE_ERROR"


class MissingEventHookConfigurationParameterError(
    MissingComponentConfigurationParameterError,
    EventHookConfigurationError,
):
    """Raised when a required parameter is not declared in an event hook's definition during
    event hook configuration.
    """

    code = "MISSING_EVENT_HOOK_CONFIGURATION_PARAMETER_ERROR"


class EmptyEventHookLabelError(
    EmptyComponentLabelError,
    EventHookConfigurationError,
):
    """Raised when an empty label is provided in an event hook's definition during event
    hook configuration.
    """

    code = "EMPTY_EVENT_HOOK_LABEL_ERROR"


class InvalidEventHookVersionError(
    InvalidComponentVersionError,
    EventHookConfigurationError,
):
    """Raised when the event hook version string provided in the event hook's definition
    is not a valid version string according to PEP 440 during event hook configuration.
    """

    code = "INVALID_EVENT_HOOK_VERSION_ERROR"


class InvalidFrameworkVersionSpecifierError(
    InvalidFrameworkVersionSpecifierError,
    EventHookConfigurationError,
):
    """Raised when the framework version specifier string provided in the event hook's
    definition is not a valid version specifier string as defined in PEP 440 during
    event hook configuration.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"


class InvalidEventHookDependencyVersionSpecifierError(
    InvalidComponentDependencyVersionSpecifierError,
    EventHookConfigurationError,
):
    """Raised when an event hook dependency version specifier string provided in the event hook's
    definition is not a valid version specifier string as defined in PEP 440 during
    event hook configuration.
    """

    code = "INVALID_EVENT_HOOK_DEPENDENCY_VERSION_SPECIFIER_ERROR"
