"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`PluginsServiceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginsServiceError]
        - [`PluginNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginNotFoundError]
        - [`PluginLoadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginLoadingError]
            - [`InvalidPluginManifestFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginManifestFileError]
                - [`InvalidPluginManifestFileJSONError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginManifestFileJSONError]
                - [`InvalidPluginManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginManifestFileSchemaError]
            - [`InvalidPluginPyProjectFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginPyProjectFileError]
            - [`InvalidPluginPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginPyProjectFileTOMLError]
            - [`InvalidPluginPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginPyProjectFileDependencyError]
            - [`InvalidPluginDirectoryStructureError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginDirectoryStructureError]
                - [`PluginManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginManifestFileNotFoundError]
                - [`PluginEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginEntryPointModuleNotFoundError]
            - [`InvalidPluginImplementationError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginImplementationError]
                - [`PluginSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginSymbolNotFoundError]
                - [`PluginInterfaceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginInterfaceError]
                - [`InternalPluginError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginError]
            - [`IncompatiblePluginFrameworkVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatiblePluginFrameworkVersionError]
            - [`PluginAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginAlreadyRegisteredError]
            - [`DuplicatePluginLabelError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.DuplicatePluginLabelError]
        - [`PluginDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.ComponentDependencyNotFoundError]
            - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatibleComponentDependencyVersionError]
            - [`PluginDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginDependsOnInvalidComponentDependencyError]
            - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.ComponentDependencyNotRunningError]
        - [`PluginUnloadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginUnloadingError]
            - [`PluginStopTimeoutError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginStopTimeoutError]

The loading, dependency, and registry exceptions below carry no `__init__` of their own: they
are constructed by the shared component loader/registry pipeline with the generic component
keyword arguments (`component_directory`, `component_str`, `component_id`, ...) inherited from
their `components_service_exceptions` base. Only the unloading errors, which are raised directly
by the plugin registry with a bespoke message, define their own constructor.
"""

from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class PluginsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the plugins service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "PLUGINS_SERVICE_ERROR"


class PluginNotFoundError(
    PluginsServiceError,
    comp_excs.ComponentNotFoundError,
):
    """Raised when the requested plugin with the provided plugin ID was not found in the
    plugins service.
    """

    code = "PLUGIN_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "plugin"


class PluginLoadingError(PluginsServiceError, comp_excs.ComponentLoadingError):
    """Base exception for all errors that occur during the loading of a plugin."""

    code = "PLUGIN_LOADING_ERROR"

    _COMPONENT_TYPE = "plugin"


class InvalidPluginManifestFileError(
    PluginLoadingError,
    comp_excs.InvalidComponentManifestFileError,
):
    """Base exception for all errors that occur due to an invalid plugin manifest
    file during plugin loading.
    """

    code = "INVALID_PLUGIN_MANIFEST_FILE_ERROR"


class InvalidPluginManifestFileJSONError(
    InvalidPluginManifestFileError,
    comp_excs.InvalidComponentManifestFileJSONError,
):
    """Raised when the plugin manifest file is not valid JSON during plugin
    loading.
    """

    code = "INVALID_PLUGIN_MANIFEST_FILE_JSON_ERROR"


class InvalidPluginManifestFileSchemaError(
    InvalidPluginManifestFileError,
    comp_excs.InvalidComponentManifestFileSchemaError,
):
    """Raised when the plugin manifest file does not conform to the expected JSON
    schema during plugin loading.
    """

    code = "INVALID_PLUGIN_MANIFEST_FILE_SCHEMA_ERROR"


class InvalidPluginPyProjectFileError(
    PluginLoadingError,
    comp_excs.InvalidComponentPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during plugin loading.
    """

    code = "INVALID_PLUGIN_PYPROJECT_FILE_ERROR"


class InvalidPluginPyProjectFileTOMLError(
    PluginLoadingError,
    comp_excs.InvalidComponentPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during plugin loading."""

    code = "INVALID_PLUGIN_PYPROJECT_FILE_TOML_ERROR"


class InvalidPluginPyProjectFileDependencyError(
    PluginLoadingError,
    comp_excs.InvalidComponentPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    plugin loading.
    """

    code = "INVALID_PLUGIN_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidPluginDirectoryStructureError(
    PluginLoadingError,
    comp_excs.InvalidComponentDirectoryStructureError,
):
    """Base exception for all errors that occur due to an invalid plugin directory
    structure during plugin loading.
    """

    code = "INVALID_PLUGIN_DIRECTORY_STRUCTURE_ERROR"


class PluginManifestFileNotFoundError(
    InvalidPluginDirectoryStructureError,
    comp_excs.ComponentManifestFileNotFoundError,
):
    """Raised when the plugin manifest file is not found in the plugin
    directory during plugin loading.
    """

    code = "PLUGIN_MANIFEST_FILE_NOT_FOUND_ERROR"


class PluginEntryPointModuleNotFoundError(
    InvalidPluginDirectoryStructureError,
    comp_excs.ComponentEntryPointModuleNotFoundError,
):
    """Raised when the plugin entry point module specified in the manifest file is not
    found in the plugin directory during plugin loading.
    """

    code = "PLUGIN_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


class InvalidPluginImplementationError(
    PluginLoadingError,
    comp_excs.InvalidComponentImplementationError,
):
    """Base exception for all errors that occur due to the plugin not implementing
    the required interface during plugin loading.
    """

    code = "INVALID_PLUGIN_IMPLEMENTATION_ERROR"


class PluginSymbolNotFoundError(
    InvalidPluginImplementationError,
    comp_excs.ComponentSymbolNotFoundError,
):
    """Raised when the plugin symbol name specified in the manifest file is not found in
    the plugin entry point module during plugin loading.
    """

    code = "PLUGIN_SYMBOL_NOT_FOUND_ERROR"


class PluginInterfaceError(
    InvalidPluginImplementationError,
    comp_excs.ComponentInterfaceError,
):
    """Raised when the plugin class does not implement the required interface during
    plugin loading.
    """

    code = "PLUGIN_INTERFACE_ERROR"


class InternalPluginError(
    InvalidPluginImplementationError,
    comp_excs.InternalComponentError,
):
    """Raised when an unhandled exception from within the plugin is raised during plugin
    loading.
    """

    code = "INTERNAL_PLUGIN_ERROR"


class IncompatiblePluginFrameworkVersionError(
    PluginLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when a plugin's required framework version is incompatible with the current
    framework version during plugin loading.
    """

    code = "INCOMPATIBLE_PLUGIN_FRAMEWORK_VERSION_ERROR"


class PluginAlreadyRegisteredError(
    PluginLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when a plugin with the same ID is already registered in the plugins service
    during plugin loading.
    """

    code = "PLUGIN_ALREADY_REGISTERED_ERROR"


class DuplicatePluginLabelError(
    PluginLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the plugin's definition is already in use by
    another plugin during plugin loading.
    """

    code = "DUPLICATE_PLUGIN_LABEL_ERROR"


class PluginDependencyError(
    PluginsServiceError,
    comp_excs.ComponentDependencyError,
):
    """Base exception for all errors that occur during the resolution of plugin
    dependencies.
    """

    code = "PLUGIN_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "plugin"


class ThirdPartyDependencyNotFoundError(
    PluginDependencyError,
    comp_excs.ThirdPartyDependencyNotFoundError,
):
    """Raised when a third-party dependency required by a plugin is not installed during
    plugin dependency resolution.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleThirdPartyDependencyVersionError(
    PluginDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the plugin during plugin dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"


class ComponentDependencyNotFoundError(
    PluginDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a plugin dependency required by the plugin is not found in the plugins
    service during plugin dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleComponentDependencyVersionError(
    PluginDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a plugin dependency's version is incompatible with the version required
    by the plugin during plugin dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"


class PluginDependsOnInvalidComponentDependencyError(
    PluginDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when a plugin depends on another plugin that itself has invalid dependencies
    during plugin dependency resolution.
    """

    code = "PLUGIN_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"


class ComponentDependencyNotRunningError(
    PluginDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a plugin dependency required by the plugin is present but not currently
    running during plugin dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"


class PluginUnloadingError(PluginsServiceError):
    """Base exception for all errors that occur during the unloading of a plugin."""

    code = "PLUGIN_UNLOADING_ERROR"


class PluginStopTimeoutError(PluginUnloadingError):
    """Raised when the plugin fails to stop within the specified timeout period during
    plugin unloading.
    """

    code = "PLUGIN_STOP_TIMEOUT_ERROR"

    def __init__(self, plugin_str: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin_str}'. The plugin timed out while "
                f"attempting to stop it before unloading."
            ),
        )
