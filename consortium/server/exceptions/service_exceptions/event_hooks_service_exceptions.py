"""
Exception hierarchy for errors related to the event hooks service:

- BaseServiceException: Base class for all service-related exceptions.
  - EventHooksServiceException: Base class for all errors related to the event hooks
  service.
    - EventHookNotFoundError: Raised when an event hook is not found.
    - EventHookLoadingError: Raised when an event hook fails to load.
      - InvalidEventHookProjectManifestFileError: Raised when the event hook project
      manifest file is invalid.
        - InvalidEventHookProjectManifestFileJSONError: Raised when the event hook
        project manifest file is not a valid JSON file.
        - InvalidEventHookProjectManifestFileSchemaError: Raised when the event hook
        project manifest file does not conform to the expected schema.
      - InvalidEventHookProjectFolderStructureError: Raised when the event hook project
      folder structure is invalid.
        - EventHookProjectManifestFileNotFoundError: Raised when the event hook project
        manifest file is not found.
        - EventHookProjectEventHookFileNotFoundError: Raised when the event hook file
        specified in the manifest is not found.
      - InvalidEventHookProjectImplementationError: Raised when an event hook project's
      implementation is invalid.
        - EventHookProjectSymbolNotFoundError: Raised when the symbol name specified in
        the manifest is not found in the event hook file.
        - EventHookProjectInterfaceError: Raised when the event hook class does not
        implement the BaseEventHook interface.
        - InternalEventHookProjectError: Raised when an internal error occurs while
        handling an event hook project.
    - EventHookUnloadingError: Raised when an event hook fails to unload.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class EventHooksServiceError(BaseServiceException):
    pass


class EventHookNotFoundError(EventHooksServiceError):
    def __init__(self, event_hook_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested event hook. No event hook was found "
                f"with the provided event hook ID '{event_hook_id}'."
            ),
        )


class EventHookLoadingError(EventHooksServiceError):
    pass


class InvalidEventHookProjectManifestFileError(EventHookLoadingError):
    pass


class InvalidEventHookProjectManifestFileJSONError(
    InvalidEventHookProjectManifestFileError,
):
    def __init__(self, event_hook_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. "
                f"The event hook project manifest file in the event hook project "
                f"folder is not a valid JSON file."
            ),
        )


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
):
    def __init__(self, event_hook_project_folder: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. "
                f"The event hook project manifest file in the event hook project "
                f"folder failed JSON schema validation: {json_schema_error_message}"
            ),
        )


class InvalidEventHookProjectFolderStructureError(EventHookLoadingError):
    pass


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
):
    def __init__(self, event_hook_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. "
                f"The event hook project manifest file was not found in the event hook "
                f"project folder."
            ),
        )


class EventHookProjectEventHookFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
):
    def __init__(self, event_hook_file: str, event_hook_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. "
                f"The event hook file '{event_hook_file}' specified in the event hook "
                f"project's manifest file was not found."
            ),
        )


class InvalidEventHookProjectImplementationError(EventHookLoadingError):
    pass


class EventHookProjectSymbolNotFoundError(InvalidEventHookProjectImplementationError):
    def __init__(
        self,
        symbol_name: str,
        event_hook_file: str,
        event_hook_project_folder: str,
    ):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. The "
                f"symbol name '{symbol_name}' specified in the event hook project's "
                f"manifest file was not found in the event hook file "
                f"'{event_hook_file}'."
            ),
        )


class EventHookProjectInterfaceError(InvalidEventHookProjectImplementationError):
    def __init__(
        self,
        event_hook_project_folder: str,
        event_hook_symbol: str,
    ):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. "
                f"The event hook in the event hook project does not implement the "
                f"required interface for its defined symbol '{event_hook_symbol}'."
            ),
        )


class InternalEventHookProjectError(InvalidEventHookProjectImplementationError):
    def __init__(
        self,
        event_hook_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to load the event hook at '{event_hook_project_folder}'. An "
                f"exception occurred while loading the event hook: {internal_error_message}"
            ),
        )


class EventHookUnloadError(EventHooksServiceError):
    def __init__(self, event_hook: str):
        super().__init__(
            message=(
                f"Failed to unload event hook '{event_hook}'. An error occurred "
                f"while unloading the event hook."
            ),
        )
