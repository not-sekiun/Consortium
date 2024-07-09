"""
Exception hierarchy for errors related to the PluginsService:

- BaseServiceException: Base class for all service-related exceptions.
  - PluginsServiceException: Base class for all errors related to the plugins service.
    - PluginNotFoundError: Raised when a plugin is not found.
    - PluginLoadingError: Raised when a plugin fails to load.
      - InvalidPluginProjectManifestFileError: Raised when the plugin project manifest
      file is invalid.
        - InvalidPluginProjectManifestFileJSONError: Raised when the plugin project
        manifest file is not a valid JSON file.
        - InvalidPluginProjectManifestFileSchemaError: Raised when the plugin project
        manifest file does not conform to the expected schema.
      - InvalidPluginProjectFolderStructureError: Raised when the plugin project folder
      structure is invalid.
        - PluginProjectManifestFileNotFoundError: Raised when the plugin project
        manifest file is not found.
        - PluginProjectPluginFileNotFoundError: Raised when the plugin file specified
        in the manifest is not found.
      - InvalidPluginProjectImplementationError: Raised when a plugin project's
      implementation is invalid.
        - PluginProjectSymbolNotFoundError: Raised when the symbol name specified in
        the manifest is not found in the plugin file.
        - PluginProjectInterfaceError: Raised when the plugin class does not implement
        the BasePlugin interface.
        - InternalPluginProjectError: Raised when an internal error occurs while
        handling a plugin project.
    - PluginUnloadingError: Raised when a plugin fails to unload.
      - InternalPluginStopError: Raised when a plugin fails to stop due to an internal
      error.
      - PluginStopTimeoutError: Raised when a plugin fails to stop due to a timeout.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class PluginsServiceError(BaseServiceException):
    pass


class PluginNotFoundError(PluginsServiceError):
    def __init__(self, plugin_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested plugin. No plugin was found with the "
                f"provided plugin ID '{plugin_id}'."
            ),
        )


class PluginLoadingError(PluginsServiceError):
    pass


class InvalidPluginProjectManifestFileError(PluginLoadingError):
    pass


class InvalidPluginProjectManifestFileJSONError(
    InvalidPluginProjectManifestFileError,
):
    def __init__(self, plugin_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin project manifest file in the plugin project folder is "
                f"not a valid JSON file."
            ),
        )


class InvalidPluginProjectManifestFileSchemaError(
    InvalidPluginProjectManifestFileError,
):
    def __init__(self, plugin_project_folder: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin project manifest file in the plugin project folder "
                f"failed JSON schema validation: {json_schema_error_message}"
            ),
        )


class InvalidPluginProjectFolderStructureError(PluginLoadingError):
    pass


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
):
    def __init__(self, plugin_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin project manifest file was not found in the plugin "
                f"project folder."
            ),
        )


class PluginProjectPluginFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
):
    def __init__(self, plugin_file: str, plugin_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin file '{plugin_file}' specified in the plugin project's "
                f"manifest file was not found."
            ),
        )


class InvalidPluginProjectImplementationError(PluginLoadingError):
    pass


class PluginProjectSymbolNotFoundError(InvalidPluginProjectImplementationError):
    def __init__(
        self,
        symbol_name: str,
        plugin_file: str,
        plugin_project_folder: str,
    ):
        super().__init__(
            message=(
                f"Failed to load plugin project at '{plugin_project_folder}'. The "
                f"symbol name '{symbol_name}' specified in the plugin project's "
                f"manifest file was not found in the plugin file '{plugin_file}'."
            ),
        )


class PluginProjectInterfaceError(InvalidPluginProjectImplementationError):
    def __init__(
        self,
        plugin_project_folder: str,
        plugin_symbol: str,
    ):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin in the plugin project does not implement the required "
                f"interface for its defined symbol '{plugin_symbol}'."
            ),
        )


class InternalPluginProjectError(InvalidPluginProjectImplementationError):
    def __init__(
        self,
        plugin_project_folder: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to load plugin project at '{plugin_project_folder}'. An "
                f"exception occurred while loading the plugin: {error_message}"
            ),
        )


class PluginUnloadError(PluginsServiceError):
    pass


class InternalPluginStopError(PluginUnloadError):
    def __init__(self, plugin: str, error_message: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin}'. An exception occurred while "
                f"stopping the plugin: {error_message}"
            ),
        )


class PluginStopTimeoutError(PluginUnloadError):
    def __init__(self, plugin: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin}'. The plugin timed out while "
                f"attempting to stop it before unloading."
            ),
        )
