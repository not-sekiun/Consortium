from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyRunningError,
    ComponentConfigurationError,
    ComponentNotRunningError,
    ComponentOperationError,
    ComponentRuntimeError,
    ComponentsFrameworkError,
    ComponentStartError,
    ComponentStateError,
    ComponentStopError,
    EmptyComponentLabelError,
    InvalidComponentConfigurationParameterTypeError,
    InvalidComponentDependencyVersionSpecifierError,
    InvalidComponentVersionError,
    InvalidFrameworkVersionSpecifierError as InvalidComponentFrameworkVersionSpecifierError,
    MissingComponentConfigurationParameterError,
)


class PluginsFrameworkError(
    ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the plugins framework."""

    code = "PLUGINS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "plugin"


class PluginConfigurationError(
    ComponentConfigurationError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur during the configuration of a particular
    plugin.
    """

    code = "PLUGIN_CONFIGURATION_ERROR"


class InvalidPluginConfigurationParameterTypeError(
    InvalidComponentConfigurationParameterTypeError,
    PluginConfigurationError,
):
    """Raised when a plugin's configuration parameter is not of the expected type during
    plugin configuration.
    """

    code = "INVALID_PLUGIN_CONFIGURATION_PARAMETER_TYPE_ERROR"


class MissingPluginConfigurationParameterError(
    MissingComponentConfigurationParameterError,
    PluginConfigurationError,
):
    """Raised when a required parameter is not declared in a plugin's definition during
    plugin configuration.
    """

    code = "MISSING_PLUGIN_CONFIGURATION_PARAMETER_ERROR"


class EmptyPluginLabelError(
    EmptyComponentLabelError,
    PluginConfigurationError,
):
    """Raised when an empty label is provided in a plugin's definition during plugin
    configuration.
    """

    code = "EMPTY_PLUGIN_LABEL_ERROR"


class InvalidPluginVersionError(
    InvalidComponentVersionError,
    PluginConfigurationError,
):
    """Raised when the plugin version string provided in the plugin's definition is not a
    valid version string according to PEP 440 during plugin configuration.
    """

    code = "INVALID_PLUGIN_VERSION_ERROR"


class InvalidFrameworkVersionSpecifierError(
    InvalidComponentFrameworkVersionSpecifierError,
    PluginConfigurationError,
):
    """Raised when the framework version specifier string provided in the plugin's
    definition is not a valid version specifier string as defined in PEP 440 during
    plugin configuration.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"


class InvalidPluginDependencyVersionSpecifierError(
    InvalidComponentDependencyVersionSpecifierError,
    PluginConfigurationError,
):
    """Raised when a plugin dependency version specifier string provided in the plugin's
    definition is not a valid version specifier string as defined in PEP 440 during
    plugin configuration.
    """

    code = "INVALID_PLUGIN_DEPENDENCY_VERSION_SPECIFIER_ERROR"


class PluginOperationError(
    ComponentOperationError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur during the operation of a particular
    plugin.
    """

    code = "PLUGIN_OPERATION_ERROR"


class PluginStartError(ComponentStartError, PluginOperationError):
    """Raised when a plugin fails to start during plugin operation."""

    code = "PLUGIN_START_ERROR"


class PluginRuntimeError(
    ComponentRuntimeError,
    PluginOperationError,
):
    """Raised when a plugin encounters an unhandled error at runtime during plugin
    operation.
    """

    code = "PLUGIN_RUNTIME_ERROR"


class PluginStopError(ComponentStopError, PluginOperationError):
    """Raised when a plugin fails to stop during plugin operation."""

    code = "PLUGIN_STOP_ERROR"


class PluginStateError(
    ComponentStateError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur due to invalid plugin status during
    plugin operation.
    """

    code = "PLUGIN_STATE_ERROR"


class PluginNotRunningError(
    ComponentNotRunningError,
    PluginStateError,
):
    """Raised when an operation is attempted on a plugin that requires the plugin to
    already be running but the plugin is not running.
    """

    code = "PLUGIN_NOT_RUNNING_ERROR"


class PluginAlreadyRunningError(
    ComponentAlreadyRunningError,
    PluginStateError,
):
    """Raised when an operation is attempted on a plugin that requires the plugin to not
    already be started or running but the plugin is already started or running.
    """

    code = "PLUGIN_ALREADY_RUNNING_ERROR"
