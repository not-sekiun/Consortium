"""
This module describes all the exceptions that can be raised by the plugins framework.
These exceptions are distinctly different from the "signalling" exceptions that are
present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
module. The exceptions here do not serve any message passing or signalling purpose to or
from the framework. Instead, they are raised when an error condition occurs and are also
meant to be used by the REST API layer.

Exception hierarchy for the plugins framework:

- [`BaseFrameworkException`][consortium.server.exceptions.framework_exceptions.base_framework_exception.BaseFrameworkException]
    - [`PluginsFrameworkError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginsFrameworkError]
        - [`PluginConfigurationError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginConfigurationError]
            - [`InvalidPluginConfigurationParameterTypeError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginConfigurationParameterTypeError]
            - [`RequiredPluginConfigurationParameterNotDeclaredError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.RequiredPluginConfigurationParameterNotDeclaredError]
            - [`EmptyPluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.EmptyPluginLabelError]
            - [`DuplicatePluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.DuplicatePluginLabelError]
            - [`InvalidPluginVersionError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginVersionError]
            - [`InvalidFrameworkVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidFrameworkVersionSpecifierError]
            - [`InvalidThirdPartyDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidThirdPartyDependencyVersionSpecifierError]
            - [`InvalidPluginDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginDependencyVersionSpecifierError]
        - [`PluginDependencyError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`PluginDependencyNotFoundError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginDependencyNotFoundError]
            - [`IncompatiblePluginDependencyVersionError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.IncompatiblePluginDependencyVersionError]
            - [`PluginDependencyNotRunningError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginDependencyNotRunningError]
        - [`PluginOperationError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginOperationError]
            - [`PluginNotRunningError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginNotRunningError]
            - [`PluginAlreadyStartedError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginAlreadyStartedError]
            - [`PluginStartError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStartError]
            - [`PluginRuntimeError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginRuntimeError]
            - [`PluginStopError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStopError]
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


class EmptyPluginLabelError(PluginConfigurationError):
    """
    An error that is raised when the label provided in a plugin's definition during
    configuration is an empty string.
    """

    def __init__(self, plugin_filepath: str):
        super().__init__(
            f"Failed to configure the plugin defined at '{plugin_filepath}'. The "
            f"label provided in the plugin's definition during configuration cannot be "
            f"empty.",
        )


class DuplicatePluginLabelError(PluginConfigurationError):
    """
    An error that is raised when the label provided in the plugin's definition during
    configuration is already in use by another plugin.
    """

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The label '{label}' is "
            "already used by another plugin.",
        )


class InvalidPluginVersionError(PluginConfigurationError):
    """
    An error that is raised when the plugin version string provided in the plugin's
    definition during configuration is invalid.
    """

    def __init__(self, plugin_str: str, version: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The plugin version "
            f"'{version}' is invalid.",
        )


class InvalidFrameworkVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the framework version specifier string provided in the
    plugin's definition during configuration is invalid.
    """

    def __init__(self, plugin_str: str, framework_version_specifier_str: str):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The framework version "
            f"specifier string '{framework_version_specifier_str}' is invalid.",
        )


class InvalidThirdPartyDependencyVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the third-party dependency version specifier string
    provided in the plugin's definition during configuration is invalid.
    """

    def __init__(
        self,
        plugin_str: str,
        third_party_dependency_name: str,
        third_party_dependency_version_specifier: str,
    ):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The third-party dependency "
            f"'{third_party_dependency_name}' version specifier string "
            f"'{third_party_dependency_version_specifier}' is invalid.",
        )


class InvalidPluginDependencyVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the plugin dependency version specifier string
    provided in the plugin's definition during configuration is invalid.
    """

    def __init__(
        self,
        plugin_str: str,
        plugin_dependency_name: str,
        plugin_dependency_version_specifier: str,
    ):
        super().__init__(
            f"Failed to configure the plugin {plugin_str}. The plugin dependency "
            f"'{plugin_dependency_name}' version specifier string "
            f"'{plugin_dependency_version_specifier}' is invalid.",
        )


class PluginDependencyError(PluginsFrameworkError):
    """
    Base exception for all errors that occur during the resolution of a plugin's
    dependencies.
    """


class ThirdPartyDependencyNotFoundError(PluginDependencyError):
    """
    An error that is raised when a third-party dependency required by a plugin is not
    installed.
    """

    def __init__(
        self,
        plugin_str: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            f"Failed to start the plugin {plugin_str} due to a dependency error. The "
            f"third-party dependency '{third_party_dependency_name}' is not installed.",
        )


class IncompatibleThirdPartyDependencyVersionError(PluginDependencyError):
    """
    An error that is raised when a third-party dependency required by a plugin is
    incompatible with the plugin.
    """

    def __init__(
        self,
        plugin_str: str,
        third_party_dependency_name: str,
        third_party_dependency_version_specifier: str,
        third_party_dependency_version: str,
    ):
        super().__init__(
            message=(
                f"Failed to start the plugin {plugin_str} due to a dependency error. "
                f"The plugin requires the third-party dependency "
                f"'{third_party_dependency_name}' of version "
                f"'{third_party_dependency_version_specifier}' but version "
                f"'{third_party_dependency_version}' is installed."
            ),
        )


class PluginDependencyNotFoundError(PluginDependencyError):
    """
    An error that is raised when a plugin dependency required by a plugin is not
    installed.
    """

    def __init__(
        self,
        plugin_str: str,
        plugin_dependency_name: str,
    ):
        super().__init__(
            f"Failed to start the plugin {plugin_str} due to a dependency error. The "
            f"plugin dependency '{plugin_dependency_name}' is not installed.",
        )


class IncompatiblePluginDependencyVersionError(PluginDependencyError):
    """
    An error that is raised when a plugin dependency required by a plugin is
    incompatible with the plugin.
    """

    def __init__(
        self,
        plugin_str: str,
        plugin_dependency_name: str,
        plugin_dependency_version_specifier: str,
        plugin_dependency_version: str,
    ):
        super().__init__(
            message=(
                f"Failed to start the plugin {plugin_str} due to a dependency error. "
                f"The plugin requires the plugin dependency "
                f"'{plugin_dependency_name}' of version "
                f"'{plugin_dependency_version_specifier}' but version "
                f"'{plugin_dependency_version}' is installed."
            ),
        )


class PluginDependencyNotRunningError(PluginDependencyError):
    """
    An error that is raised when a plugin dependency required by a plugin is present but
    not currently running.
    """

    def __init__(
        self,
        plugin_str: str,
        plugin_dependency_name: str,
    ):
        super().__init__(
            f"Failed to start the plugin {plugin_str} due to a dependency error. The "
            f"plugin dependency '{plugin_dependency_name}' that the plugin depends on "
            f"is installed but not currently running.",
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
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the plugin "
                f"{plugin_str}. The plugin is not running."
            ),
        )


class PluginAlreadyStartedError(PluginOperationError):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to not already be started or running but the plugin is already started
    or running.
    """

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the plugin "
                f"{plugin_str}. The plugin is already started or running."
            ),
        )


class PluginStartError(PluginOperationError):
    """
    An error that is raised when a plugin fails to start.
    """

    def __init__(
        self,
        plugin_str: str,
        message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to start the plugin {plugin_str}. {message}",
            detail=detail,
        )


class PluginRuntimeError(PluginOperationError):
    """
    An error that is raised when a plugin encounters an error at runtime.
    """

    def __init__(
        self,
        plugin_str: str,
        message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"Failed to run the plugin {plugin_str} because it encountered an "
                f"error at runtime. {message}"
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
        message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to stop the plugin {plugin_str}. {message}",
            detail=detail,
        )
