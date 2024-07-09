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
    pass


class ListenerProfileNotFoundError(ListenerProfilesServiceError):
    def __init__(self, listener_profile_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested listener profile. No listener profile "
                f"was found with the provided listener profile ID "
                f"'{listener_profile_id}'."
            ),
        )


class ListenerProfileLoadError(ListenerProfilesServiceError):
    pass


class InvalidListenerProjectManifestFileError(ListenerProfileLoadError):
    pass


class InvalidListenerProjectManifestFileJSONError(
    InvalidListenerProjectManifestFileError,
):
    def __init__(self, listener_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the listener project at '{listener_project_folder}'. "
                f"The listener project manifest file in the listener project folder is "
                f"not a valid JSON file."
            ),
        )


class InvalidListenerProjectManifestFileSchemaError(
    InvalidListenerProjectManifestFileError,
):
    def __init__(self, listener_project_folder: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the listener project at '{listener_project_folder}'. "
                f"The listener project manifest file in the listener project folder "
                f"failed JSON schema validation: {json_schema_error_message}"
            ),
        )


class InvalidListenerProjectFolderStructureError(ListenerProfileLoadError):
    pass


class ListenerProjectManifestFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the listener project at '{listener_project_folder}'. "
                f"The listener project manifest file was not found in the listener "
                f"project folder."
            ),
        )


class ListenerProjectListenerFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_file: str, listener_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the listener project at "
                f"'{listener_project_folder}'. The listener file '{listener_file}' "
                "specified in the listener project's manifest file was not found."
            ),
        )


class ListenerProjectListenerTemplateFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_template_file: str, listener_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the listener project at "
                f"'{listener_project_folder}'. The listener template file "
                f"'{listener_template_file}' specified in the listener project's "
                f"manifest file was not found."
            ),
        )


class ListenerProjectListenerTypeFileNotFoundError(
    InvalidListenerProjectFolderStructureError,
):
    def __init__(self, listener_type_file: str, listener_project_folder: str):
        super().__init__(
            f"Failed to load the listener project at '{listener_project_folder}'. The "
            f"listener type file '{listener_type_file}' specified in the listener "
            f"project's manifest file was not found.",
        )


class InvalidListenerProjectImplementationError(ListenerProfileLoadError):
    pass


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
            f"Failed to load the listener project at '{listener_project_folder}'. "
            f"The {listener_project_file_type} in the listener project does not "
            f"implement the required interface for its defined symbol "
            f"'{listener_project_symbol}'.",
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
            f"Failed to load listener project at '{listener_project_folder}'. The "
            f"symbol name '{symbol_name}' specified in the listener project's manifest "
            f"file was not found in the {listener_project_file_type} file "
            f"'{listener_project_file}'.",
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
        error_message: str,
    ):
        super().__init__(
            f"Failed to load listener project at '{listener_project_folder}'. An "
            f"exception occurred while loading the "
            f"{listener_project_file_type}: {error_message}",
        )
