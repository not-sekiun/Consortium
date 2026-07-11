from typing import Any

from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions,
)


class PluginsFrameworkError(
    components_framework_exceptions.ComponentsFrameworkError,
):
    """Base exception for all errors that occur within the plugins framework."""

    code = "PLUGINS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "plugin"


class PluginConfigurationError(
    components_framework_exceptions.ComponentConfigurationError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur during the configuration of a particular
    plugin.
    """

    code = "PLUGIN_CONFIGURATION_ERROR"


class InvalidPluginConfigurationParameterTypeError(
    components_framework_exceptions.InvalidComponentConfigurationParameterTypeError,
    PluginConfigurationError,
):
    """Raised when a plugin's configuration parameter is not of the expected type during
    plugin configuration.
    """

    code = "INVALID_PLUGIN_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        plugin_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=plugin_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingPluginConfigurationParameterError(
    components_framework_exceptions.MissingComponentConfigurationParameterError,
    PluginConfigurationError,
):
    """Raised when a required parameter is not declared in a plugin's definition during
    plugin configuration.
    """

    code = "MISSING_PLUGIN_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, plugin_str: str, parameter_name: str):
        super().__init__(
            component_str=plugin_str,
            parameter_name=parameter_name,
        )


class EmptyPluginLabelError(
    components_framework_exceptions.EmptyComponentLabelError,
    PluginConfigurationError,
):
    """Raised when an empty label is provided in a plugin's definition during plugin
    configuration.
    """

    code = "EMPTY_PLUGIN_LABEL_ERROR"

    def __init__(self, plugin_filepath: str):
        super().__init__(component_filepath=plugin_filepath)


class InvalidPluginVersionError(
    components_framework_exceptions.InvalidComponentVersionError,
    PluginConfigurationError,
):
    """Raised when the plugin version string provided in the plugin's definition is not a
    valid version string according to PEP 440 during plugin configuration.
    """

    code = "INVALID_PLUGIN_VERSION_ERROR"

    def __init__(self, plugin_str: str, version: str):
        super().__init__(
            component_str=plugin_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    components_framework_exceptions.InvalidFrameworkVersionSpecifierError,
    PluginConfigurationError,
):
    """Raised when the framework version specifier string provided in the plugin's
    definition is not a valid version specifier string as defined in PEP 440 during
    plugin configuration.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(self, plugin_str: str, framework_version_specifier: str):
        super().__init__(
            component_str=plugin_str,
            framework_version_specifier=framework_version_specifier,
        )


class InvalidPluginDependencyVersionSpecifierError(
    components_framework_exceptions.InvalidComponentDependencyVersionSpecifierError,
    PluginConfigurationError,
):
    """Raised when a plugin dependency version specifier string provided in the plugin's
    definition is not a valid version specifier string as defined in PEP 440 during
    plugin configuration.
    """

    code = "INVALID_PLUGIN_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        plugin_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=plugin_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class PluginOperationError(
    components_framework_exceptions.ComponentOperationError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur during the operation of a particular
    plugin.
    """

    code = "PLUGIN_OPERATION_ERROR"


class PluginStartError(
    components_framework_exceptions.ComponentStartError, PluginOperationError
):
    """Raised when a plugin fails to start during plugin operation."""

    code = "PLUGIN_START_ERROR"

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=plugin_str,
            error_message=error_message,
        )


class PluginRuntimeError(
    components_framework_exceptions.ComponentRuntimeError,
    PluginOperationError,
):
    """Raised when a plugin encounters an unhandled error at runtime during plugin
    operation.
    """

    code = "PLUGIN_RUNTIME_ERROR"

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=plugin_str,
            error_message=error_message,
        )


class PluginStopError(
    components_framework_exceptions.ComponentStopError, PluginOperationError
):
    """Raised when a plugin fails to stop during plugin operation."""

    code = "PLUGIN_STOP_ERROR"

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=plugin_str,
            error_message=error_message,
        )


class PluginStateError(
    components_framework_exceptions.ComponentStateError,
    PluginsFrameworkError,
):
    """Base exception for all errors that occur due to invalid plugin status during
    plugin operation.
    """

    code = "PLUGIN_STATE_ERROR"


class PluginNotRunningError(
    components_framework_exceptions.ComponentNotRunningError,
    PluginStateError,
):
    """Raised when an operation is attempted on a plugin that requires the plugin to
    already be running but the plugin is not running.
    """

    code = "PLUGIN_NOT_RUNNING_ERROR"

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)


class PluginAlreadyRunningError(
    components_framework_exceptions.ComponentAlreadyRunningError,
    PluginStateError,
):
    """Raised when an operation is attempted on a plugin that requires the plugin to not
    already be started or running but the plugin is already started or running.
    """

    code = "PLUGIN_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)
