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


class PluginsServiceException(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the plugins service.",
    ):
        super().__init__(message)


class PluginNotFoundError(PluginsServiceException):
    def __init__(self, plugin_id: str):
        super().__init__(
            f"Failed to find the requested plugin. No plugin was found with the "
            f"provided plugin ID '{plugin_id}'.",
        )


class PluginLoadError(PluginsServiceException):
    def __init__(
        self,
        message: str = "Failed to load plugin. An error occurred while loading the "
        "plugin.",
    ):
        super().__init__(message)


class InvalidPluginProjectManifestFileError(PluginLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load plugin project. The plugin project manifest file is "
            "invalid."
        ),
    ):
        super().__init__(message)


class InvalidPluginProjectManifestFileJSONError(
    InvalidPluginProjectManifestFileError,
):
    def __init__(self, plugin_project_folder: str):
        super().__init__(
            "Failed to load plugin project. The plugin project manifest file in "
            f"plugin project folder '{plugin_project_folder}' is not a valid JSON "
            f"file.",
        )


class InvalidPluginProjectManifestFileSchemaError(
    InvalidPluginProjectManifestFileError,
):
    def __init__(self, plugin_project_folder: str, json_schema_error_message: str):
        super().__init__(
            "Failed to load plugin project. The plugin project manifest file in "
            f"plugin project folder '{plugin_project_folder}' failed when "
            f"validating against the JSON schema: {json_schema_error_message}",
        )


class InvalidPluginProjectFolderStructureError(PluginLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load plugin project folder. The plugin project folder "
            "structure is invalid."
        ),
    ):
        super().__init__(message)


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
):
    def __init__(self, plugin_project_folder: str):
        super().__init__(
            "Failed to load plugin project. The plugin project manifest file was "
            f"not found in the plugin project folder '{plugin_project_folder}'.",
        )


class PluginProjectPluginFileNotFoundError(InvalidPluginProjectFolderStructureError):
    def __init__(self, plugin_file: str, plugin_project_folder: str):
        super().__init__(
            f"Failed to load plugin project folder. Plugin file '{plugin_file}' "
            "specified in the plugin project manifest file is missing for plugin "
            f"project folder '{plugin_project_folder}'.",
        )


class InvalidPluginProjectImplementationError(PluginLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load plugin. The plugin project implementation is " "invalid."
        ),
    ):
        super().__init__(message)


class PluginProjectSymbolNotFoundError(InvalidPluginProjectImplementationError):
    def __init__(self, symbol_name: str, plugin_file: str, plugin_project_folder: str):
        super().__init__(
            f"Failed to load plugin project. The symbol name '{symbol_name}' "
            "specified in the plugin project manifest file was not found in the "
            f"plugin file '{plugin_file}' for plugin project folder "
            f"'{plugin_project_folder}'",
        )


class PluginProjectInterfaceError(InvalidPluginProjectImplementationError):
    def __init__(self, plugin_symbol: str, plugin_project_folder: str):
        super().__init__(
            f"Failed to load plugin. The plugin in plugin project folder "
            f"'{plugin_project_folder}' does not implement the required interface for "
            f"its symbol '{plugin_symbol}'.",
        )


class InternalPluginProjectError(InvalidPluginProjectImplementationError):
    def __init__(self, plugin_project_folder: str, internal_error_message: str):
        super().__init__(
            "Failed to load plugin. An exception was raised when loading the plugin "
            f"from plugin project folder '{plugin_project_folder}': "
            f"{internal_error_message}",
        )


class PluginUnloadError(PluginsServiceException):
    def __init__(
        self,
        message: str = "Failed to unload plugin. An error occurred while unloading "
        "the plugin.",
    ):
        super().__init__(message)


class InternalPluginStopError(PluginUnloadError):
    def __init__(self, plugin_name: str, internal_error_message: str):
        super().__init__(
            "Failed to unload plugin. An exception was raised when unloading the "
            f"plugin '{plugin_name}': {internal_error_message}",
        )


class PluginStopTimeoutError(PluginUnloadError):
    def __init__(self, plugin_name):
        super().__init__(
            f"Failed to unload plugin. The plugin '{plugin_name}' timed out while "
            f"attempting to stop it before unloading it.",
        )
