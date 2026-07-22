"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`PluginsServiceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginsServiceError]
        - [`PluginNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginNotFoundError]
        - [`PluginLoadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginLoadingError]
            - [`InvalidPluginProjectManifestFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileError]
                - [`InvalidPluginProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileJSONError]
                - [`InvalidPluginProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileSchemaError]
            - [`InvalidPluginProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileError]
            - [`InvalidPluginProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileTOMLError]
            - [`InvalidPluginProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileDependencyError]
            - [`InvalidPluginProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectFolderStructureError]
                - [`PluginProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectManifestFileNotFoundError]
                - [`PluginProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectEntryPointModuleNotFoundError]
            - [`InvalidPluginProjectImplementationError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectImplementationError]
                - [`PluginProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectSymbolNotFoundError]
                - [`PluginProjectInterfaceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectInterfaceError]
                - [`InternalPluginProjectError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginProjectError]
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


class InvalidPluginProjectManifestFileError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectManifestFileError,
):
    """Base exception for all errors that occur due to an invalid plugin project manifest
    `manifest.json` file during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_ERROR"


class InvalidPluginProjectManifestFileJSONError(
    InvalidPluginProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileJSONError,
):
    """Raised when the plugin project manifest file is not valid JSON during plugin
    loading.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_JSON_ERROR"


class InvalidPluginProjectManifestFileSchemaError(
    InvalidPluginProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the plugin project manifest file does not conform to the expected JSON
    schema during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"


class InvalidPluginProjectPyProjectFileError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidPluginProjectPyProjectFileTOMLError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during plugin loading."""

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_TOML_ERROR"


class InvalidPluginProjectPyProjectFileDependencyError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidPluginProjectFolderStructureError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid plugin root directory
    structure during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_FOLDER_STRUCTURE_ERROR"


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the plugin project manifest file is not found in the plugin root
    directory during plugin loading.
    """

    code = "PLUGIN_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"


class PluginProjectEntryPointModuleNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the plugin entry point module specified in the manifest is not found in
    the plugin root directory during plugin loading.
    """

    code = "PLUGIN_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


class InvalidPluginProjectImplementationError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectImplementationError,
):
    """Base exception for all errors that occur due to the plugin project not implementing
    the required interface during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_IMPLEMENTATION_ERROR"


class PluginProjectSymbolNotFoundError(
    InvalidPluginProjectImplementationError,
    comp_excs.ComponentProjectSymbolNotFoundError,
):
    """Raised when the plugin symbol name specified in the manifest is not found in the
    plugin entry point module during plugin loading.
    """

    code = "PLUGIN_PROJECT_SYMBOL_NOT_FOUND_ERROR"


class PluginProjectInterfaceError(
    InvalidPluginProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the plugin class does not implement the required interface during
    plugin loading.
    """

    code = "PLUGIN_PROJECT_INTERFACE_ERROR"


class InternalPluginProjectError(
    InvalidPluginProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the plugin is raised during plugin
    loading.
    """

    code = "INTERNAL_PLUGIN_PROJECT_ERROR"


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
