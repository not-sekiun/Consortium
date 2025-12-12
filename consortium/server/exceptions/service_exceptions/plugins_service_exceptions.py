"""
Exception hierarchy for the plugins service:

- [`BaseServiceException`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
    - [`PluginsServiceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginsServiceError]
        - [`PluginNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginNotFoundError]
        - [`PluginLabelNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginLabelNotFoundError]
        - [`PluginLoadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginLoadingError]
            - [`InvalidPluginProjectManifestFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileError]
                - [`InvalidPluginProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileJSONError]
                - [`InvalidPluginProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileSchemaError]
            - [`InvalidPluginProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileError]
                - [`InvalidPluginProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileTOMLError]
                - [`InvalidPluginProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectPyProjectFileDependencyError]
            - [`InvalidPluginProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectFolderStructureError]
                - [`PluginProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectManifestFileNotFoundError]
                - [`PluginProjectPluginFileNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectPluginFileNotFoundError]
            - [`InvalidPluginProjectImplementationError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectImplementationError]
                - [`PluginProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectSymbolNotFoundError]
                - [`PluginProjectInterfaceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginProjectInterfaceError]
                - [`InternalPluginProjectError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginProjectError]
            - [`IncompatiblePluginFrameworkVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatiblePluginFrameworkVersionError]
            - [`PluginAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginAlreadyRegisteredError]
            - [`DuplicatePluginLabelError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.DuplicatePluginLabelError]
            - [`InternalPluginStartError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginStartError]
        - [`PluginDependencyError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`PluginDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginDependencyNotFoundError]
            - [`IncompatiblePluginDependencyVersionError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.IncompatiblePluginDependencyVersionError]
            - [`PluginDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginDependencyNotRunningError]
        - [`PluginUnloadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginUnloadingError]
            - [`InternalPluginStopError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginStopError]
            - [`PluginStopTimeoutError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginStopTimeoutError]
"""

from consortium.server.exceptions.service_exceptions import (
    component_service_exceptions as comp_ldr_svc_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class PluginsServiceError(BaseServiceException):
    """
    Base exception for all errors that occur within the plugins service.
    """

    code = "PLUGINS_SERVICE_ERROR"


class PluginNotFoundError(
    PluginsServiceError,
    comp_ldr_svc_excs.ComponentNotFoundError,
):
    """
    An error that is raised when a plugin is not found by its plugin ID within the
    plugins service.
    """

    code = "PLUGIN_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "plugin"

    def __init__(self, plugin_id: str):
        super().__init__(component_id=plugin_id)


# class PluginLabelNotFoundError(PluginsServiceError):
#     """
#     An error that is raised when a plugin is not found by its label within the plugins
#     service.
#     """
#
#     def __init__(self, label: str):
#         super().__init__(
#             message=(
#                 f"Failed to find the requested plugin. No plugin was found with the "
#                 f"provided plugin label '{label}'."
#             ),
#         )


class PluginLoadingError(PluginsServiceError, comp_ldr_svc_excs.ComponentLoadingError):
    """
    Base exception for all errors that occur during the loading of a plugin.
    """

    code = "PLUGIN_LOADING_ERROR"

    _COMPONENT_TYPE = "plugin"


class InvalidPluginProjectManifestFileError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectManifestFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid plugin project
    manifest `manifest.json` file.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_ERROR"


class InvalidPluginProjectManifestFileJSONError(
    InvalidPluginProjectManifestFileError,
    comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError,
):
    """
    An error that is raised when the plugin project manifest file is not a valid JSON
    file.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class InvalidPluginProjectManifestFileSchemaError(
    InvalidPluginProjectManifestFileError,
    comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """
    An error that is raised when the plugin project manifest file does not conform to
    the expected JSON schema.
    """

    code = "INVALID_PLUGIN_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(self, plugin_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidPluginProjectPyProjectFileError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid `pyproject.toml`
    file.
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidPluginProjectPyProjectFileTOMLError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """
    An error that is raised when the `pyproject.toml` file is not a valid TOML file
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_TOML_ERROR"

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class InvalidPluginProjectPyProjectFileDependencyError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """
    An error that is raised when the `pyproject.toml` file contains invalid dependency
    entries.
    """

    code = "INVALID_PLUGIN_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(self, plugin_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidPluginProjectFolderStructureError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectFolderStructureError,
):
    """
    Base exception for all errors that occur due to the plugin being loaded having an
    invalid plugin project folder structure.
    """

    code = "INVALID_PLUGIN_PROJECT_FOLDER_STRUCTURE_ERROR"


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError,
):
    """
    An error that is raised when the plugin project manifest file is not found in the
    plugin project folder.
    """

    code = "PLUGIN_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, plugin_project_folder: str):
        super().__init__(component_project_folder=plugin_project_folder)


class PluginProjectEntryPointModuleNotFoundError(
    InvalidPluginProjectFolderStructureError,
    comp_ldr_svc_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """
    An error that is raised when the plugin file specified in the manifest is not
    found in the plugin project folder.
    """

    code = "PLUGIN_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(self, plugin_project_folder: str, entry_point_module: str):
        super().__init__(
            component_project_folder=plugin_project_folder,
            entry_point_module=entry_point_module,
        )


class InvalidPluginProjectImplementationError(
    PluginLoadingError,
    comp_ldr_svc_excs.InvalidComponentProjectImplementationError,
):
    """
    Base exception for all errors that occur due to the plugin project not implementing
    the required interface for the plugin.
    """

    code = "INVALID_PLUGIN_PROJECT_IMPLEMENTATION_ERROR"


class PluginProjectSymbolNotFoundError(
    InvalidPluginProjectImplementationError,
    comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError,
):
    """
    An error that is raised when the plugin symbol name specified in the manifest is not
    found in the plugin file.
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
    comp_ldr_svc_excs.ComponentProjectInterfaceError,
):
    """
    An error that is raised when the plugin class does not implement the required
    interface for the plugin.
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
    comp_ldr_svc_excs.InternalComponentProjectError,
):
    """
    An error that is raised when an unhandled exception from within the plugin is
    raised while loading a plugin project.
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
    comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError,
):
    """
    An error that is raised when a plugin is incompatible with the current framework
    version.
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
    comp_ldr_svc_excs.ComponentAlreadyRegisteredError,
):
    """
    An error that is raised when a plugin with the same ID is already registered in the
    plugins service.
    """

    code = "PLUGIN_ALREADY_REGISTERED_ERROR"

    def __init__(self, plugin_str: str, plugin_id: str):
        super().__init__(component_str=plugin_str, component_id=plugin_id)


class DuplicatePluginLabelError(
    PluginLoadingError,
    comp_ldr_svc_excs.DuplicateComponentLabelError,
):
    """
    An error that is raised when a plugin with the same `label` as the plugin being
    registered has already been registered with the plugins service.
    """

    code = "DUPLICATE_PLUGIN_LABEL_ERROR"

    def __init__(self, plugin_str: str, label: str):
        super().__init__(
            component_str=plugin_str,
            label=label,
        )


# class InternalPluginStartError(
#     PluginLoadingError,
#     # comp_ldr_svc_excs.InternalComponentStartError,
# ):
#     """
#     An error that is raised when an unhandled exception from within the plugin is
#     raised while starting a plugin.
#     """
#
#     code = "INTERNAL_PLUGIN_START_ERROR"
#
#     def __init__(self, plugin_str: str, internal_error_message: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the plugin '{plugin_str}'. An exception occurred "
#                 f"while starting the plugin: {internal_error_message}"
#             ),
#         )


class PluginDependencyError(
    PluginsServiceError,
    comp_ldr_svc_excs.ComponentDependencyError,
):
    """
    Base exception for all errors that occur during the resolution of a plugin's
    dependencies.
    """

    code = "PLUGIN_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "plugin"


class ThirdPartyDependencyNotFoundError(
    PluginDependencyError,
    comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is not
    installed.
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
    comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is
    incompatible with the plugin.
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
    comp_ldr_svc_excs.ComponentDependencyNotFoundError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is not
    installed.
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
    comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is
    incompatible with the plugin.
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
    comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """
    An error that is raised when a plugin depends on another plugin dependency that
    itself has invalid dependencies.
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
    comp_ldr_svc_excs.ComponentDependencyNotRunningError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is present but
    not currently running.
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
    """
    Base exception for all errors that occur during the unloading of a plugin.
    """

    code = "PLUGIN_UNLOADING_ERROR"


# class InternalPluginStopError(PluginUnloadingError):
#     """
#     An error that is raised when an unhandled exception from within the plugin is
#     raised while stopping a plugin.
#     """
#
#     code = "INTERNAL_PLUGIN_STOP_ERROR"
#
#     def __init__(self, plugin_str: str, internal_error_message: str):
#         super().__init__(
#             message=(
#                 f"Failed to unload plugin '{plugin_str}'. An exception occurred while "
#                 f"stopping the plugin: {internal_error_message}"
#             ),
#         )


class PluginStopTimeoutError(PluginUnloadingError):
    """
    An error that is raised when a plugin fails to stop within the specified timeout
    period.
    """

    code = "PLUGIN_STOP_TIMEOUT_ERROR"

    def __init__(self, plugin_str: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin_str}'. The plugin timed out while "
                f"attempting to stop it before unloading."
            ),
        )
