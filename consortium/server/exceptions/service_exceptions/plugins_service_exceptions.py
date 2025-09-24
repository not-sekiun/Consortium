"""
Exception hierarchy for the plugins service:

- [`BaseServiceException`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
    - [`PluginsServiceError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginsServiceError]
        - [`PluginNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginNotFoundError]
        - [`PluginLabelNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.        - [`PluginNotFoundError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginNotFoundError]
]
        - [`PluginLoadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginLoadingError]
            - [`InvalidPluginProjectManifestFileError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileError]
                - [`InvalidPluginProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileJSONError]
                - [`InvalidPluginProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InvalidPluginProjectManifestFileSchemaError]
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
        - [`PluginUnloadingError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginUnloadingError]
            - [`InternalPluginStopError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.InternalPluginStopError]
            - [`PluginStopTimeoutError`][consortium.server.exceptions.service_exceptions.plugins_service_exceptions.PluginStopTimeoutError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class PluginsServiceError(BaseServiceException):
    """
    Base exception for all errors that occur within the plugins service.
    """


class PluginNotFoundError(PluginsServiceError):
    """
    An error that is raised when a plugin is not found by its plugin ID within the
    plugins service.
    """

    def __init__(self, plugin_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested plugin. No plugin was found with the "
                f"provided plugin ID '{plugin_id}'."
            ),
        )


class PluginLabelNotFoundError(PluginsServiceError):
    """
    An error that is raised when a plugin is not found by its label within the plugins
    service.
    """

    def __init__(self, label: str):
        super().__init__(
            message=(
                f"Failed to find the requested plugin. No plugin was found with the "
                f"provided plugin label '{label}'."
            ),
        )


class PluginLoadingError(PluginsServiceError):
    """
    Base exception for all errors that occur during the loading of a plugin.
    """


class InvalidPluginProjectManifestFileError(PluginLoadingError):
    """
    Base exception for all errors that occur due to loading an invalid plugin project
    manifest file.
    """


class InvalidPluginProjectManifestFileJSONError(
    InvalidPluginProjectManifestFileError,
):
    """
    An error that is raised when the plugin project manifest file is not a valid JSON
    file.
    """

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
    """
    An error that is raised when the plugin project manifest file does not conform to
    the expected JSON schema.
    """

    def __init__(self, plugin_project_folder: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin project manifest file in the plugin project folder "
                f"failed JSON schema validation: {json_schema_error_message}"
            ),
        )


class InvalidPluginProjectFolderStructureError(PluginLoadingError):
    """
    Base exception for all errors that occur due to the plugin being loaded having an
    invalid plugin project folder structure.
    """


class PluginProjectManifestFileNotFoundError(
    InvalidPluginProjectFolderStructureError,
):
    """
    An error that is raised when the plugin project manifest file is not found in the
    plugin project folder.
    """

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
    """
    An error that is raised when the plugin file specified in the manifest is not
    found in the plugin project folder.
    """

    def __init__(self, plugin_file: str, plugin_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the plugin project at '{plugin_project_folder}'. "
                f"The plugin file '{plugin_file}' specified in the plugin project's "
                f"manifest file was not found."
            ),
        )


class InvalidPluginProjectImplementationError(PluginLoadingError):
    """
    Base exception for all errors that occur due to the plugin project not implementing
    the required interface for the plugin.
    """


class PluginProjectSymbolNotFoundError(InvalidPluginProjectImplementationError):
    """
    An error that is raised when the plugin symbol name specified in the manifest is not
    found in the plugin file.
    """

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
    """
    An error that is raised when the plugin class does not implement the required
    interface for the plugin.
    """

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
    """
    An error that is raised when an unhandled exception from within the plugin is
    raised while loading a plugin project.
    """

    def __init__(
        self,
        plugin_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to load plugin project at '{plugin_project_folder}'. An "
                f"exception occurred while loading the plugin: {internal_error_message}"
            ),
        )


class IncompatiblePluginFrameworkVersionError(PluginLoadingError):
    """
    An error that is raised when a plugin is incompatible with the current framework
    version.
    """

    def __init__(
        self,
        plugin_str: str,
        plugin_framework_version: str,
        framework_version: str,
    ):
        super().__init__(
            f"Failed to load the plugin {plugin_str}. The plugin requires a framework "
            f"version of '{plugin_framework_version}' which is incompatible with "
            f"the current framework version '{framework_version}'.",
        )


class PluginAlreadyRegisteredError(PluginLoadingError):
    """
    An error that is raised when a plugin with the same ID is already registered in the
    plugins service.
    """

    def __init__(self, plugin_str: str, plugin_id: str):
        super().__init__(
            message=(
                f"Failed to register the plugin '{plugin_str}'. A plugin with the same ID "
                f"'{plugin_id}' has already been registered in the plugins service."
            ),
        )


class DuplicatePluginLabelError(PluginLoadingError):
    """
    An error that is raised when a plugin with the same `label` as the plugin being
    registered has already been registered with the plugins service.
    """

    def __init__(self, plugin_str: str, plugin_label: str):
        super().__init__(
            message=(
                f"Failed to register the plugin '{plugin_str}'. A plugin with the same "
                f"label '{plugin_label}' has already been registered in the plugins "
                f"service."
            ),
        )


class InternalPluginStartError(PluginLoadingError):
    """
    An error that is raised when an unhandled exception from within the plugin is
    raised while starting a plugin.
    """

    def __init__(self, plugin_str: str, internal_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the plugin '{plugin_str}'. An exception occurred while "
                f"starting the plugin: {internal_error_message}"
            ),
        )


class PluginUnloadingError(PluginsServiceError):
    """
    Base exception for all errors that occur during the unloading of a plugin.
    """


class InternalPluginStopError(PluginUnloadingError):
    """
    An error that is raised when an unhandled exception from within the plugin is
    raised while stopping a plugin.
    """

    def __init__(self, plugin_str: str, internal_error_message: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin_str}'. An exception occurred while "
                f"stopping the plugin: {internal_error_message}"
            ),
        )


class PluginStopTimeoutError(PluginUnloadingError):
    """
    An error that is raised when a plugin fails to stop within the specified timeout
    period.
    """

    def __init__(self, plugin_str: str):
        super().__init__(
            message=(
                f"Failed to unload plugin '{plugin_str}'. The plugin timed out while "
                f"attempting to stop it before unloading."
            ),
        )
