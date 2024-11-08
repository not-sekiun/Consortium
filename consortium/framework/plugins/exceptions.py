"""
This module describes all the exceptions that can be raised by the plugins framework.
These exceptions are distinctly different from the "signalling" exceptions that are
present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
module. The exceptions here do not serve any message passing or signalling purpose to or
from the framework. Instead, they are raised when an error condition occurs and are also
meant to be used by the REST API layer.

The exception hierarchy for the plugins framework is as follows:

- [`BaseFrameworkException`][consortium.server.exceptions.framework_exceptions.base_framework_exception.BaseFrameworkException]
    - [`PluginsFrameworkError`][consortium.framework.plugins.exceptions.PluginsFrameworkError]
        - [`PluginConfigurationError`][consortium.framework.plugins.exceptions.PluginConfigurationError]
            - [`InvalidPluginConfigurationParameterTypeError`][consortium.framework.plugins.exceptions.InvalidPluginConfigurationParameterTypeError]
            - [`RequiredPluginConfigurationParameterNotDeclaredError`][consortium.framework.plugins.exceptions.RequiredPluginConfigurationParameterNotDeclaredError]
            - [`EmptyPluginNameError`][consortium.framework.plugins.exceptions.EmptyPluginNameError]
            - [`DuplicatePluginNameError`][consortium.framework.plugins.exceptions.DuplicatePluginNameError]
            - [`InvalidPluginVersionError`]consortium.framework.plugins.exceptions.InvalidPluginVersionError]
            - [`InvalidFrameworkVersionSpecifierError`][consortium.framework.plugins.exceptions.InvalidFrameworkVersionSpecifierError]
        - [`PluginOperationError`][consortium.framework.plugins.exceptions.PluginOperationError]
            - [`PluginNotRunningError`][consortium.framework.plugins.exceptions.PluginNotRunningError]
            - [`PluginAlreadyRunningError`][consortium.framework.plugins.exceptions.PluginAlreadyRunningError]
            - [`PluginStartError`][consortium.framework.plugins.exceptions.PluginStartError]
            - [`PluginRuntimeError`][consortium.framework.plugins.exceptions.PluginRuntimeError]
            - [`PluginStopError`][consortium.framework.plugins.exceptions.PluginStopError]
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginsFrameworkError(BaseFrameworkException):
    """
    Base exception for all errors that occur within the plugins framework.
    """


class PluginConfigurationError(PluginsFrameworkError):
    """
    Base exception for all errors that occur during the configuration of a particular
    plugin.
    """


class InvalidPluginConfigurationParameterTypeError(PluginConfigurationError):
    """
    An error that is raised when a plugin's configuration parameter is of an invalid
    type.
    """

    def __init__(
        self,
        plugin_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the plugin {plugin_str}. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"plugin's definition."
                ),
            )
        else:
            super().__init__(
                f"Failed to configure the plugin {plugin_str}. {error_message}",
            )


class RequiredPluginConfigurationParameterNotDeclaredError(PluginConfigurationError):
    """
    An error that is raised when a required parameter is not declared in a plugin's
    definition.
    """

    def __init__(self, parameter_name: str, plugin_str: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The required parameter "
            f"'{parameter_name}' was not declared in the plugin's definition.",
        )


class EmptyPluginNameError(PluginConfigurationError):
    """
    An error that is raised when the name provided in a plugin's definition during
    configuration is an empty string.
    """

    def __init__(self, plugin_filepath: str):
        super().__init__(
            f"Failed to configure the plugin defined at '{plugin_filepath}'. The "
            f"name provided in the plugin's definition during configuration cannot be "
            f"empty.",
        )


class DuplicatePluginNameError(PluginConfigurationError):
    """
    An error that is raised when the name provided in the plugin's definition during
    configuration is already in use by another plugin.
    """
    def __init__(self, plugin_str: str, name: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The name '{name}' is "
            "already used by another plugin."
        )


class InvalidPluginVersionError(PluginConfigurationError):
    """
    An error that is raised when the plugin version string provided in the plugin's
    definition during configuration is invalid.
    """
    def __init__(self, plugin_str: str, plugin_version_str: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The plugin version "
            f"string '{plugin_version_str}' is invalid."
        )


class InvalidFrameworkVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the framework version specifier string provided in the
    plugin's definition during configuration is invalid.
    """
    def __init__(self, plugin_str: str, framework_version_specifier_str: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The framework version "
            f"specifier string '{framework_version_specifier_str}' is invalid."
        )


class PluginOperationError(PluginsFrameworkError):
    """
    Base exception for all errors that occur during the operation of a particular
    plugin.
    """


class PluginNotRunningError(PluginOperationError):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to already be running but the plugin is not running.
    """

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the plugin {plugin_str} "
                f"because it is not running. {error_message}"
            ),
        )


class PluginAlreadyRunningError(PluginOperationError):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to not already be running but the plugin is already running.
    """

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the plugin {plugin_str} "
                f"because it is already running. {error_message}"
            ),
        )


class PluginStartError(PluginOperationError):
    """
    An error that is raised when a plugin fails to start.
    """

    def __init__(
        self,
        plugin_str: str,
        start_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to start the plugin {plugin_str}. {start_error_message}",
            detail=detail,
        )


class PluginRuntimeError(PluginOperationError):
    """
    An error that is raised when a plugin encounters an error at runtime.
    """

    def __init__(
        self,
        plugin_str: str,
        runtime_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to run the plugin {plugin_str} because it encountered an error "
                f"at runtime. {runtime_error_message}"
            ),
            detail=detail,
        )


class PluginStopError(PluginOperationError):
    """
    An error that is raised when a plugin fails to stop.
    """

    def __init__(
        self,
        plugin_str: str,
        stop_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to stop the plugin {plugin_str}. {stop_error_message}",
            detail=detail,
        )
