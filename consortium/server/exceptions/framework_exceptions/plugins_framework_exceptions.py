"""
Exception hierarchy for plugins framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - PluginsFrameworkError: A general error occurred in the plugins framework.
    - PluginConfigurationError: Error occurred during plugin configuration.
      - PluginConfigurationParameterError: Error with a plugin configuration parameter.
        - PluginConfigurationParameterTypeError: Invalid type for a plugin
        configuration parameter.
        - RequiredPluginConfigurationParameterNotDeclaredError: Required parameter not
        declared in plugin configuration.
        - EmptyPluginNameError: The name provided for a plugin is an empty string.
    - PluginNotRunningError: An error occurred because the requested operation
    could not be completed while the plugin is not running.
    - PluginAlreadyRunningError: An error occurred because the requested
    operation could not be completed while the plugin is running.
    - PluginStartError: Error occurred while attempting to start a plugin.
    - PluginRuntimeError: Error occurred during plugin execution.
    - PluginStopError: Error occurred while attempting to stop a plugin.
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginsFrameworkError(BaseFrameworkException):
    pass


class PluginConfigurationError(PluginsFrameworkError):
    pass


class PluginConfigurationParameterError(PluginConfigurationError):
    pass


class PluginConfigurationParameterTypeError(
    PluginConfigurationParameterError,
):
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
                    f"Failed to configure the plugin '{plugin_str}'. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"plugin's definition."
                ),
            )
        else:
            super().__init__(
                f"Failed to configure the plugin '{plugin_str}'. {error_message}",
            )


class RequiredPluginConfigurationParameterNotDeclaredError(
    PluginConfigurationParameterError,
):
    def __init__(self, parameter_name: str, plugin_str: str):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The required parameter "
            f"'{parameter_name}' was not declared in the plugin's definition.",
        )


class EmptyPluginNameError(PluginConfigurationParameterError):
    def __init__(self, plugin_filepath: str):
        super().__init__(
            f"Failed to configure the plugin defined at '{plugin_filepath}'. The "
            f"name provided in the plugin's definition during configuration cannot be "
            f"empty.",
        )


class PluginNotRunningError(PluginsFrameworkError):
    def __init__(
        self,
        plugin: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the plugin '{plugin}' because it is not "
                f"running. {error_message}"
            ),
        )


class PluginAlreadyRunningError(PluginsFrameworkError):
    def __init__(
        self,
        plugin: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the plugin '{plugin}' because it is "
                f"already running. {error_message}"
            ),
        )


class PluginStartError(PluginsFrameworkError):
    def __init__(
        self,
        plugin: str,
        start_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to start the plugin '{plugin}'. {start_error_message}",
            detail=detail,
        )


class PluginRuntimeError(PluginsFrameworkError):
    def __init__(
        self,
        plugin: str,
        runtime_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"The plugin '{plugin}' encountered an error while running. "
                f"{runtime_error_message}"
            ),
            detail=detail,
        )


class PluginStopError(PluginsFrameworkError):
    def __init__(
        self,
        plugin: str,
        stop_error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(f"Failed to stop the plugin '{plugin}'. {stop_error_message}"),
            detail=detail,
        )
