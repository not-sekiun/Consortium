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


class EventHooksServiceException(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the event hooks service.",
    ):
        super().__init__(message)


class EventHookNotFoundError(EventHooksServiceException):
    def __init__(self, event_hook_id: str):
        super().__init__(
            f"Failed to find the requested event hook. No event hook was found "
            f"with the provided event hook ID '{event_hook_id}'.",
        )


class EventHookLoadingError(EventHooksServiceException):
    def __init__(
        self,
        message: str = "Failed to load event hook. An error occurred while loading "
        "the event hook.",
    ):
        super().__init__(message)


class InvalidEventHookProjectManifestFileError(EventHookLoadingError):
    def __init__(
        self,
        message: str = (
            "Failed to load event hook project. The event hook project manifest "
            "file is invalid."
        ),
    ):
        super().__init__(message)


class InvalidEventHookProjectManifestFileJSONError(
    InvalidEventHookProjectManifestFileError,
):
    def __init__(self, event_hook_project_folder: str):
        super().__init__(
            "Failed to load event hook project. The event hook project manifest "
            f"file in event hook project folder '{event_hook_project_folder}' is "
            f"not a valid JSON file.",
        )


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
):
    def __init__(self, event_hook_project_folder: str, json_schema_error_message: str):
        super().__init__(
            "Failed to load event hook project. The event hook project manifest "
            f"file in event hook project folder '{event_hook_project_folder}' "
            f"failed when validating against the JSON schema: "
            f"{json_schema_error_message}",
        )


class InvalidEventHookProjectFolderStructureError(EventHookLoadingError):
    def __init__(
        self,
        message: str = (
            "Failed to load event hook project folder. The event hook project "
            "folder structure is invalid."
        ),
    ):
        super().__init__(message)


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
):
    def __init__(self, event_hook_project_folder: str):
        super().__init__(
            "Failed to load event hook project. The event hook project manifest "
            f"file was not found in the event hook project folder "
            f"'{event_hook_project_folder}'.",
        )


class EventHookProjectEventHookFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
):
    def __init__(self, event_hook_file: str, event_hook_project_folder: str):
        super().__init__(
            f"Failed to load event hook project folder. Event hook file "
            f"'{event_hook_file}' specified in the event hook project manifest "
            f"file is missing for event hook project folder "
            f"'{event_hook_project_folder}'.",
        )


class InvalidEventHookProjectImplementationError(EventHookLoadingError):
    def __init__(
        self,
        message: str = (
            "Failed to load event hook. The event hook project implementation is "
            "invalid."
        ),
    ):
        super().__init__(message)


class EventHookProjectSymbolNotFoundError(InvalidEventHookProjectImplementationError):
    def __init__(
        self,
        symbol_name: str,
        event_hook_file: str,
        event_hook_project_folder: str,
    ):
        super().__init__(
            f"Failed to load event hook project. The symbol name '{symbol_name}' "
            "specified in the event hook project manifest file was not found in "
            f"the event hook file '{event_hook_file}' for event hook project "
            f"folder '{event_hook_project_folder}'",
        )


class EventHookProjectInterfaceError(InvalidEventHookProjectImplementationError):
    def __init__(self, event_hook_symbol: str, event_hook_project_folder: str):
        super().__init__(
            f"Failed to load event hook. The event hook in event hook project folder "
            f"'{event_hook_project_folder}' does not implement the required interface "
            f"for its symbol '{event_hook_symbol}'.",
        )


class InternalEventHookProjectError(InvalidEventHookProjectImplementationError):
    def __init__(self, event_hook_project_folder: str, internal_error_message: str):
        super().__init__(
            f"Failed to load event hook. An exception was raised when loading the "
            f"event hook from event hook project folder '{event_hook_project_folder}': "
            f"{internal_error_message}",
        )


class EventHookUnloadingError(EventHooksServiceException):
    def __init__(
        self,
        message: str = "Failed to unload event hook. An error occurred while unloading "
        "the event hook.",
    ):
        super().__init__(message)
