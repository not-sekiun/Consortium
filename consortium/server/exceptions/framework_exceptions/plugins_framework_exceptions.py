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
            - [`MissingPluginConfigurationParameterError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.MissingPluginConfigurationParameterError]
            - [`EmptyPluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.EmptyPluginLabelError]
            - [`DuplicatePluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.DuplicatePluginLabelError]
            - [`InvalidPluginVersionError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginVersionError]
            - [`InvalidFrameworkVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidFrameworkVersionSpecifierError]
            - [`InvalidThirdPartyDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidThirdPartyDependencyVersionSpecifierError]
            - [`InvalidPluginDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginDependencyVersionSpecifierError]
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
        custom_error_message: str = "",
    ):
        if not custom_error_message:
            super().__init__(
                message=(
                    f"Failed to configure the plugin '{plugin_str}'. The parameter "
                    f"`{parameter_name}` must be of type `{parameter_type}` in the "
                    f"plugin's definition. Modify the plugin's `{parameter_name}` "
                    f"class variable to be of the proper type."
                ),
            )
        else:
            super().__init__(
                f"Failed to configure the plugin '{plugin_str}'. {custom_error_message}",
            )


class MissingPluginConfigurationParameterError(PluginConfigurationError):
    """
    An error that is raised when a parameter is not declared in a plugin's definition.
    """

    def __init__(self, parameter_name: str, plugin_str: str):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The parameter "
            f"`{parameter_name}` was not declared in the plugin's definition. Modify "
            f"the plugin to include `{parameter_name}` as a class variable of the "
            f"proper type",
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
            f"an empty string. Redeclare the plugin's `label` class attribute to be a "
            f"unique non empty string.",
        )


class DuplicatePluginLabelError(PluginConfigurationError):
    """
    An error that is raised when the label provided in the plugin's definition during
    configuration is already in use by another plugin.
    """

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The label '{label}' is "
            "already used by another plugin. Redeclare the plugin's `label` class "
            "attribute to be unique amongst all loaded plugins.",
        )


class InvalidPluginVersionError(PluginConfigurationError):
    """
    An error that is raised when the plugin version string provided in the plugin's
    definition during configuration is not a valid version string according to PEP 440.
    """

    def __init__(self, plugin_str: str, version: str):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The plugin version string "
            f"provided '{version}' is not a valid versioning string. See PEP 440 for "
            f"more details on valid versioning strings.",
        )


class InvalidFrameworkVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the framework version specifier string provided in the
    plugin's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    def __init__(self, plugin_str: str, framework_version_specifier_str: str):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The framework version "
            f"specifier string provided '{framework_version_specifier_str}' is not a "
            "valid version specifier string. See PEP 440 for details on version "
            "specifier strings.",
        )


class InvalidThirdPartyDependencyVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the third-party dependency version specifier string
    provided in the plugin's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    def __init__(
        self,
        plugin_str: str,
        third_party_dependency_name: str,
        third_party_dependency_version_specifier: str,
    ):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The third-party dependency "
            f"'{third_party_dependency_name}' version specifier string provided "
            f"'{third_party_dependency_version_specifier}' is not a "
            "valid version specifier string. See PEP 440 for details on version "
            "specifier strings.",
        )


class InvalidPluginDependencyVersionSpecifierError(PluginConfigurationError):
    """
    An error that is raised when the plugin dependency version specifier string
    provided in the plugin's definition during configuration is not a valid version
    specifier string as defined in PEP440..
    """

    def __init__(
        self,
        plugin_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            f"Failed to configure the plugin '{plugin_str}'. The plugin's "
            f"`plugin_dependencies` configuration parameter contains the invalid "
            f"dependency entry '{invalid_dependency_entry}'. Check that the dependency "
            f"parameter contains entries conforming to PEP 508.",
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
