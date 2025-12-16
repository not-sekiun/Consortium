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
#             - [`PluginAlreadyRunningError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginAlreadyRunningError]
#             - [`PluginStartError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStartError]
#             - [`PluginRuntimeError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginRuntimeError]
#             - [`PluginStopError`][consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions.PluginStopError]
# """
from typing import Any

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_framework_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class PluginsFrameworkError(
    comp_framework_excs.ComponentsFrameworkError,
    BaseFrameworkException,
):
    """
    Base exception for all errors that occur within the plugins framework.
    """

    code = "PLUGINS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "plugin"


class PluginConfigurationError(
    comp_framework_excs.ComponentConfigurationError,
    PluginsFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    plugin.
    """

    code = "PLUGIN_CONFIGURATION_ERROR"


class InvalidPluginConfigurationParameterTypeError(
    comp_framework_excs.InvalidComponentConfigurationParameterTypeError,
    PluginConfigurationError,
):
    """
    An error that is raised when a plugin's configuration parameter is of an invalid
    type.
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
    comp_framework_excs.MissingComponentConfigurationParameterError,
    PluginConfigurationError,
):
    """
    An error that is raised when a parameter is not declared in a plugin's definition.
    """

    code = "MISSING_PLUGIN_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, plugin_str: str, parameter_name: str):
        super().__init__(
            component_str=plugin_str,
            parameter_name=parameter_name,
        )


class EmptyPluginLabelError(
    comp_framework_excs.EmptyComponentLabelError,
    PluginConfigurationError,
):
    """
    An error that is raised when the label provided in a plugin's definition during
    configuration is an empty string.
    """

    code = "EMPTY_PLUGIN_LABEL_ERROR"

    def __init__(self, plugin_filepath: str):
        super().__init__(component_filepath=plugin_filepath)


class DuplicatePluginLabelError(
    comp_framework_excs.DuplicateComponentLabelError,
    PluginConfigurationError,
):
    """
    An error that is raised when the label provided in the plugin's definition during
    configuration is already in use by another plugin.
    """

    code = "DUPLICATE_PLUGIN_LABEL_ERROR"

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            component_str=plugin_str,
            label=label,
        )


class InvalidPluginVersionError(
    comp_framework_excs.InvalidComponentVersionError,
    PluginConfigurationError,
):
    """
    An error that is raised when the plugin version string provided in the plugin's
    definition during configuration is not a valid version string according to PEP 440.
    """

    code = "INVALID_PLUGIN_VERSION_ERROR"

    def __init__(self, plugin_str: str, version: str):
        super().__init__(
            component_str=plugin_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    comp_framework_excs.InvalidFrameworkVersionSpecifierError,
    PluginConfigurationError,
):
    """
    An error that is raised when the framework version specifier string provided in the
    plugin's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(self, plugin_str: str, framework_version_specifier: str):
        super().__init__(
            component_str=plugin_str,
            framework_version_specifier=framework_version_specifier,
        )


class InvalidPluginDependencyVersionSpecifierError(
    comp_framework_excs.InvalidComponentDependencyVersionSpecifierError,
    PluginConfigurationError,
):
    """
    An error that is raised when the plugin dependency version specifier string
    provided in the plugin's definition during configuration is not a valid version
    specifier string as defined in PEP440.
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
    comp_framework_excs.ComponentOperationError,
    PluginsFrameworkError,
):
    """
    Base exception for all errors that occur during the operation of a particular
    plugin.
    """

    code = "PLUGIN_OPERATION_ERROR"


class PluginNotRunningError(
    comp_framework_excs.ComponentNotRunningError,
    PluginOperationError,
):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to already be running but the plugin is not running.
    """

    code = "PLUGIN_NOT_RUNNING_ERROR"

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)


class PluginAlreadyRunningError(
    comp_framework_excs.ComponentAlreadyRunningError,
    PluginOperationError,
):
    """
    An error that is raised when an operation is attempted on a plugin that requires
    that plugin to not already be started or running but the plugin is already started
    or running.
    """

    code = "PLUGIN_ALREADY_RUNNING_ERROR"

    def __init__(
        self,
        plugin_str: str,
    ):
        super().__init__(component_str=plugin_str)


class PluginStartError(comp_framework_excs.ComponentStartError, PluginOperationError):
    """
    An error that is raised when a plugin fails to start.
    """

    code = "PLUGIN_START_ERROR"

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


class PluginRuntimeError(
    comp_framework_excs.ComponentRuntimeError,
    PluginOperationError,
):
    """
    An error that is raised when a plugin encounters an error at runtime.
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


class PluginStopError(comp_framework_excs.ComponentStopError, PluginOperationError):
    """
    An error that is raised when a plugin fails to stop.
    """

    code = "PLUGIN_STOP_ERROR"

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
