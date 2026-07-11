"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`PluginsError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginsError]
        - [`PluginsServiceError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginsServiceError]
            - [`PluginNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginNotFoundError]
            - [`PluginLoadingError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginLoadingError]
                - [`InvalidPluginProjectManifestFileError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectManifestFileError]
                    - [`InvalidPluginProjectManifestFileJSONError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectManifestFileJSONError]
                    - [`InvalidPluginProjectManifestFileSchemaError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectManifestFileSchemaError]
                - [`InvalidPluginProjectPyProjectFileError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectPyProjectFileError]
                - [`InvalidPluginProjectPyProjectFileTOMLError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectPyProjectFileTOMLError]
                - [`InvalidPluginProjectPyProjectFileDependencyError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectPyProjectFileDependencyError]
                - [`InvalidPluginProjectFolderStructureError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectFolderStructureError]
                    - [`PluginProjectManifestFileNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginProjectManifestFileNotFoundError]
                    - [`PluginProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginProjectEntryPointModuleNotFoundError]
                - [`InvalidPluginProjectImplementationError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InvalidPluginProjectImplementationError]
                    - [`PluginProjectSymbolNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginProjectSymbolNotFoundError]
                    - [`PluginProjectInterfaceError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginProjectInterfaceError]
                    - [`InternalPluginProjectError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.InternalPluginProjectError]
                - [`IncompatiblePluginFrameworkVersionError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.IncompatiblePluginFrameworkVersionError]
                - [`PluginAlreadyRegisteredError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginAlreadyRegisteredError]
                - [`DuplicatePluginLabelError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.DuplicatePluginLabelError]
            - [`PluginDependencyError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginDependencyError]
                - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.ThirdPartyDependencyNotFoundError]
                - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.IncompatibleThirdPartyDependencyVersionError]
                - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.ComponentDependencyNotFoundError]
                - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.IncompatibleComponentDependencyVersionError]
                - [`PluginDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginDependsOnInvalidComponentDependencyError]
                - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.ComponentDependencyNotRunningError]
            - [`PluginUnloadingError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginUnloadingError]
                - [`PluginStopTimeoutError`][consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions.PluginStopTimeoutError]
"""

from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class PluginsError(BaseConsortiumError):
    """Base exception for all plugins related errors.

    All exceptions that inherit from `PluginsError` define, `code`, `message`, and
    `detail` attributes. For brevity, `message` and `detail` are omitted within
    the documentation here.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            error that occurred.
        message: A human-readable message that describes the error.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the error.
    """

    code = "PLUGINS_ERROR"


class PluginsServiceError(PluginsError):
    """Base exception for all errors that occur within the plugins service."""

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

    def __init__(self, plugin_id: str):
        super().__init__(component_id=plugin_id)


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

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class InvalidPluginProjectManifestFileSchemaError(
    InvalidPluginProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the plugin project manifest file does not conform to the expected JSON
    schema during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(self, plugin_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


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

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class InvalidPluginProjectPyProjectFileDependencyError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(self, plugin_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidPluginProjectFolderStructureError(
    PluginLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid plugin project folder
    structure during plugin loading.
    """

    code = "INVALID_PLUGIN_PROJECT_FOLDER_STRUCTURE_ERROR"


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the plugin project manifest file is not found in the plugin project
    folder during plugin loading.
    """

    code = "PLUGIN_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class PluginProjectEntryPointModuleNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the plugin entry point module specified in the manifest is not found in
    the plugin project folder during plugin loading.
    """

    code = "PLUGIN_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(self, plugin_project_folder: str, entry_point_module: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            entry_point_module=entry_point_module,
        )


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

    def __init__(
        self,
        plugin_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=plugin_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class PluginProjectInterfaceError(
    InvalidPluginProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the plugin class does not implement the required interface during
    plugin loading.
    """

    code = "PLUGIN_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        plugin_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_project_folder=plugin_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalPluginProjectError(
    InvalidPluginProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the plugin is raised during plugin
    loading.
    """

    code = "INTERNAL_PLUGIN_PROJECT_ERROR"

    def __init__(
        self,
        plugin_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_project_folder=plugin_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatiblePluginFrameworkVersionError(
    PluginLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when a plugin's required framework version is incompatible with the current
    framework version during plugin loading.
    """

    code = "INCOMPATIBLE_PLUGIN_FRAMEWORK_VERSION_ERROR"

    def __init__(
        self,
        plugin_str: str,
        required_version: str,
        current_version: str,
    ):
        super().__init__(
            component_str=plugin_str,
            required_version=required_version,
            current_version=current_version,
        )


class PluginAlreadyRegisteredError(
    PluginLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when a plugin with the same ID is already registered in the plugins service
    during plugin loading.
    """

    code = "PLUGIN_ALREADY_REGISTERED_ERROR"

    def __init__(self, plugin_str: str, plugin_id: str):
        super().__init__(component_str=plugin_str, component_id=plugin_id)


class DuplicatePluginLabelError(
    PluginLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the plugin's definition is already in use by
    another plugin during plugin loading.
    """

    code = "DUPLICATE_PLUGIN_LABEL_ERROR"

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            component_str=plugin_str,
            label=label,
        )


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

    def __init__(
        self,
        plugin_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_project_folder=plugin_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(
    PluginDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the plugin during plugin dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        plugin_project_folder: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_project_folder=plugin_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(
    PluginDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a plugin dependency required by the plugin is not found in the plugins
    service during plugin dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        plugin_str: str,
        missing_dependency: str,
    ):
        super().__init__(
            component_str=plugin_str,
            missing_dependency=missing_dependency,
        )


class IncompatibleComponentDependencyVersionError(
    PluginDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a plugin dependency's version is incompatible with the version required
    by the plugin during plugin dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        plugin_str: str,
        incompatible_dependency: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_str=plugin_str,
            incompatible_dependency=incompatible_dependency,
            required_version=required_version,
            installed_version=installed_version,
        )


class PluginDependsOnInvalidComponentDependencyError(
    PluginDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when a plugin depends on another plugin that itself has invalid dependencies
    during plugin dependency resolution.
    """

    code = "PLUGIN_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"

    def __init__(
        self,
        plugin_str: str,
        invalid_dependency: str,
    ):
        super().__init__(
            component_str=plugin_str,
            invalid_dependency=invalid_dependency,
        )


class ComponentDependencyNotRunningError(
    PluginDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a plugin dependency required by the plugin is present but not currently
    running during plugin dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"

    def __init__(
        self,
        plugin_str: str,
        not_running_dependency: str,
    ):
        super().__init__(
            component_str=plugin_str,
            not_running_dependency=not_running_dependency,
        )


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
