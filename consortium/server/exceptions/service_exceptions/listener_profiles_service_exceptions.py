"""
Exception hierarchy for errors related to listener projects:

- BaseServiceException: Base class for all service-related exceptions.
  - ListenerProfilesServiceError: Base class for all errors related to the listener
  profiles service.
    - ListenerProfileNotFoundError: Raised when a listener profile is not found.
    - ListenerProfileLoadError: Raised when a listener profile fails to load.
      - InvalidListenerProjectManifestFileError: Raised when the listener project
      manifest file is invalid.
        - ListenerProjectManifestFileInvalidJSONError: Raised when the listener project
        manifest file is not a valid JSON file.
        - ListenerProjectManifestFileSchemaError: Raised when the listener project
        manifest file does not conform to the expected schema.
      - InvalidListenerProjectFolderStructureError: Raised when the listener project
      folder structure is invalid.
        - ListenerProjectManifestFileNotFoundError: Raised when the listener project
        manifest file is not found.
        - ListenerProjectListenerFileNotFoundError: Raised when the listener file
        specified in the manifest is not found.
        - ListenerProjectListenerTemplateFileNotFoundError: Raised when the listener
        template file specified in the manifest is not found.
        - ListenerProjectListenerTypeFileNotFoundError: Raised when the listener type
        file specified in the manifest is not found.
      - InvalidListenerProjectImplementationError: Raised when a listener project's
      implementation is invalid.
        - ListenerProjectInterfaceError: Raised when a symbol (listener, listener
        template, or listener type) does not implement its respective interface.
        - ListenerProjectSymbolNotFoundError: Raised when a symbol (listener, listener
        template, or listener type) is not found.
        - InternalListenerProjectError: Raised when an internal error occurs while
        handling a listener project.
"""

from typing import Literal

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenerProfilesServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the listener profiles service.",
    ):
        super().__init__(message)


class ListenerProfileNotFoundError(ListenerProfilesServiceError):
    def __init__(self, listener_profile_id: str):
        super().__init__(
            "Failed to find the requested listener profile. No listener profile was "
            f"found with the provided listener profile ID '{listener_profile_id}'.",
        )


class ListenerProfileLoadError(ListenerProfilesServiceError):
    def __init__(
        self,
        message: str = "Failed to load listener profile. An error occurred while "
        "loading the listener profile.",
    ):
        super().__init__(message)


class InvalidListenerProjectManifestFileError(ListenerProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load listener project. The listener project manifest file is "
            "invalid."
        ),
    ):
        super().__init__(message)


class InvalidListenerProjectManifestFileJSONError(
    InvalidListenerProjectManifestFileError,
):
    def __init__(self, listener_project_folder: str):
        super().__init__(
            "Failed to load listener project. The listener project manifest file "
            f"in listener project folder '{listener_project_folder}' is not a valid "
            f"JSON file.",
        )


class InvalidListenerProjectManifestFileSchemaError(
    InvalidListenerProjectManifestFileError,
):
    def __init__(self, listener_project_folder: str, json_schema_error_message: str):
        super().__init__(
            "Failed to load listener project. The listener project manifest file in "
            f"listener project folder '{listener_project_folder}' failed when "
            f"validating against the JSON schema: {json_schema_error_message}",
        )


class InvalidListenerProjectFolderStructureError(ListenerProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load listener project folder. The listener project "
            "folder structure is invalid."
        ),
    ):
        super().__init__(message)


class ListenerProjectManifestFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_project_folder: str):
        super().__init__(
            "Failed to load listener project. The listener project manifest file was "
            f"not found in the listener project folder '{listener_project_folder}'.",
        )


class ListenerProjectListenerFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_file: str, listener_project_folder: str):
        super().__init__(
            f"Failed to load listener project folder. Listener file '{listener_file}' "
            "specified in the listener project manifest file is missing for listener "
            f"project folder '{listener_project_folder}'.",
        )


class ListenerProjectListenerTemplateFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_template_file: str, listener_project_folder: str):
        super().__init__(
            "Failed to load listener project folder. The listener template file "
            f"'{listener_template_file}' specified in the listener project manifest "
            f"file is missing for listener project folder '{listener_project_folder}'.",
        )


class ListenerProjectListenerTypeFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_type_file: str, listener_project_folder: str):
        super().__init__(
            "Failed to load listener project folder. The listener type file "
            f"'{listener_type_file}' specified in the listener project manifest file "
            f"is missing for listener project folder '{listener_project_folder}'",
        )


class InvalidListenerProjectImplementationError(ListenerProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load listener profile. The listener project implementation is "
            "invalid."
        ),
    ):
        super().__init__(message)


class ListenerProjectInterfaceError(InvalidListenerProjectImplementationError):
    def __init__(
        self,
        listener_project_file_type: Literal[
            "listener",
            "listener template",
            "listener type",
        ],
        listener_project_folder: str,
        listener_project_symbol: str,
    ):
        super().__init__(
            f"Failed to load listener profile. The {listener_project_file_type} in "
            f"listener project folder '{listener_project_folder}' does not implement "
            f"the required interface for its symbol '{listener_project_symbol}'.",
        )


class ListenerProjectSymbolNotFoundError(InvalidListenerProjectImplementationError):
    def __init__(
        self,
        symbol_name: str,
        listener_project_file: str,
        listener_project_folder: str,
        listener_project_file_type: Literal[
            "listener",
            "listener template",
            "listener type",
        ],
    ):
        super().__init__(
            f"Failed to load listener project. The symbol name '{symbol_name}' "
            "specified in the listener project manifest file was not found in the "
            f"{listener_project_file_type} file '{listener_project_file}' for listener "
            f"project folder '{listener_project_folder}'",
        )


class InternalListenerProjectError(InvalidListenerProjectImplementationError):
    def __init__(
        self,
        listener_project_file_type: Literal[
            "listener",
            "listener template",
            "listener type",
        ],
        listener_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            "Failed to load listener profile. An exception occurred while loading the "
            f"{listener_project_file_type} from listener project folder "
            f"'{listener_project_folder}': {internal_error_message}",
        )
