# """
# This module describes all the exceptions that can be raised by the plugins framework.
# These exceptions are distinctly different from the "signalling" exceptions that are
# present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
# module. The exceptions here do not serve any message passing or signalling purpose to or
# from the framework. Instead, they are raised when an error condition occurs and are also
# meant to be used by the REST API layer.
#
# Exception hierarchy for the plugins framework:
#
# - [`BaseFrameworkException`][consortium.server.exceptions.framework_exceptions.base_framework_exception.BaseFrameworkException]
#     - [`PluginsFrameworkError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginsFrameworkError]
#         - [`PluginConfigurationError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginConfigurationError]
#             - [`InvalidPluginConfigurationParameterTypeError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginConfigurationParameterTypeError]
#             - [`MissingPluginConfigurationParameterError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.MissingPluginConfigurationParameterError]
#             - [`EmptyPluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.EmptyPluginLabelError]
#             - [`DuplicatePluginLabelError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.DuplicatePluginLabelError]
#             - [`InvalidPluginVersionError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginVersionError]
#             - [`InvalidFrameworkVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidFrameworkVersionSpecifierError]
#             - [`InvalidThirdPartyDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidThirdPartyDependencyVersionSpecifierError]
#             - [`InvalidPluginDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.InvalidPluginDependencyVersionSpecifierError]
#         - [`PluginOperationError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginOperationError]
#             - [`PluginNotRunningError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginNotRunningError]
#             - [`PluginAlreadyStartedError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginAlreadyStartedError]
#             - [`PluginStartError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStartError]
#             - [`PluginRuntimeError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginRuntimeError]
#             - [`PluginStopError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStopError]
# """
from typing import Any

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginsFrameworkError(comp_excs.ComponentsFrameworkError, BaseFrameworkException):
    """
    Base exception for all errors that occur within the plugins framework.
    """

    _COMPONENT_TYPE = "plugin"


class PluginConfigurationError(
    comp_excs.ComponentConfigurationError,
    PluginsFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    plugin.
    """


class InvalidPluginConfigurationParameterTypeError(
    comp_excs.InvalidComponentConfigurationParameterTypeError,
    PluginConfigurationError,
):
    """
    An error that is raised when a plugin's configuration parameter is of an invalid
    type.
    """

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
    comp_excs.MissingComponentConfigurationParameterError,
    PluginConfigurationError,
):
    """
    An error that is raised when a parameter is not declared in a plugin's definition.
    """

    def __init__(self, parameter_name: str, plugin_str: str):
        super().__init__(
            component_str=plugin_str,
            parameter_name=parameter_name,
        )


class EmptyPluginLabelError(
    comp_excs.EmptyComponentLabelError,
    PluginConfigurationError,
):
    """
    An error that is raised when the label provided in a plugin's definition during
    configuration is an empty string.
    """

    def __init__(self, plugin_filepath: str):
        super().__init__(component_filepath=plugin_filepath)


class DuplicatePluginLabelError(
    comp_excs.DuplicateComponentLabelError,
    PluginConfigurationError,
):
    """
    An error that is raised when the label provided in the plugin's definition during
    configuration is already in use by another plugin.
    """

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            component_str=plugin_str,
            label=label,
        )


class InvalidPluginVersionError(
    comp_excs.InvalidComponentVersionError,
    PluginConfigurationError,
):
    """
    An error that is raised when the plugin version string provided in the plugin's
    definition during configuration is not a valid version string according to PEP 440.
    """

    def __init__(self, plugin_str: str, version: str):
        super().__init__(
            component_str=plugin_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    comp_excs.InvalidFrameworkVersionSpecifierError,
    PluginConfigurationError,
):
    """
    An error that is raised when the framework version specifier string provided in the
    plugin's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    def __init__(self, plugin_str: str, framework_version_specifier_str: str):
        super().__init__(
            component_str=plugin_str,
            framework_version_specifier_str=framework_version_specifier_str,
        )


class InvalidPluginDependencyVersionSpecifierError(
    comp_excs.InvalidComponentDependencyVersionSpecifierError,
    PluginConfigurationError,
):
    """
    An error that is raised when the plugin dependency version specifier string
    provided in the plugin's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    def __init__(
        self,
        plugin_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=plugin_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class PluginOperationError(comp_excs.ComponentOperationError, PluginsFrameworkError):
    """
    Base exception for all errors that occur during the operation of a particular
    plugin.
    """


class PluginNotRunningError(comp_excs.ComponentNotRunningError, PluginOperationError):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to already be running but the plugin is not running.
    """

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)


class PluginAlreadyStartedError(
    comp_excs.ComponentAlreadyStartedError,
    PluginOperationError,
):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to not already be started or running but the plugin is already started
    or running.
    """

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)


class PluginStartError(comp_excs.ComponentStartError, PluginOperationError):
    """
    An error that is raised when a plugin fails to start.
    """

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            plugin_str=plugin_str,
            error_message=error_message,
        )


class PluginRuntimeError(comp_excs.ComponentRuntimeError, PluginOperationError):
    """
    An error that is raised when a plugin encounters an error at runtime.
    """

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


class PluginStopError(comp_excs.ComponentStopError, PluginOperationError):
    """
    An error that is raised when a plugin fails to stop.
    """

    def __init__(
        self,
        plugin_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            plugin_str=plugin_str,
            error_message=error_message,
        )
