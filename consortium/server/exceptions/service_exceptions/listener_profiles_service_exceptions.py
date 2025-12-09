# """
# Exception hierarchy for errors related to listener projects:
#
# - BaseServiceException: Base class for all service-related exceptions.
#   - ListenerProfilesServiceError: Base class for all errors related to the listener
#   profiles service.
#     - ListenerProfileNotFoundError: Raised when a listener profile is not found.
#     - ListenerProfileLoadError: Raised when a listener profile fails to load.
#       - InvalidListenerProjectManifestFileError: Raised when the listener project
#       manifest file is invalid.
#         - ListenerProjectManifestFileInvalidJSONError: Raised when the listener project
#         manifest file is not a valid JSON file.
#         - ListenerProjectManifestFileSchemaError: Raised when the listener project
#         manifest file does not conform to the expected schema.
#       - InvalidListenerProjectFolderStructureError: Raised when the listener project
#       folder structure is invalid.
#         - ListenerProjectManifestFileNotFoundError: Raised when the listener project
#         manifest file is not found.
#         - ListenerProjectListenerFileNotFoundError: Raised when the listener file
#         specified in the manifest is not found.
#         - ListenerProjectListenerTemplateFileNotFoundError: Raised when the listener
#         template file specified in the manifest is not found.
#         - ListenerProjectListenerTypeFileNotFoundError: Raised when the listener type
#         file specified in the manifest is not found.
#       - InvalidListenerProjectImplementationError: Raised when a listener project's
#       implementation is invalid.
#         - ListenerProjectInterfaceError: Raised when a symbol (listener, listener
#         template, or listener type) does not implement its respective interface.
#         - ListenerProjectSymbolNotFoundError: Raised when a symbol (listener, listener
#         template, or listener type) is not found.
#         - InternalListenerProjectError: Raised when an internal error occurs while
#         handling a listener project.
# """
from consortium.server.exceptions.service_exceptions import (
    component_service_exceptions as comp_svc_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenerProfilesServiceError(BaseServiceException):
    code = "LISTENER_PROFILES_SERVICE_ERROR"


class ListenerProfileNotFoundError(
    ListenerProfilesServiceError,
    comp_svc_excs.ComponentNotFoundError,
):
    """
    An error that is raised when a listener profile is not found in the listener
    profiles service.
    """

    code = "LISTENER_PROFILE_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "listener profile"

    def __init__(self, listener_profile_id: str):
        super().__init__(component_id=listener_profile_id)


class ListenerProfileLoadingError(
    ListenerProfilesServiceError,
    comp_svc_excs.ComponentLoadingError,
):
    """
    Base exception for all errors that occur during the loading of a listener profile.
    """

    code = "LISTENER_PROFILE_LOADING_ERROR"

    _COMPONENT_TYPE = "listener profile"


class InvalidListenerProfileProjectManifestFileError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectManifestFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid listener profile project
    manifest `manifest.json` file.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_ERROR"


class InvalidListenerProfileProjectManifestFileJSONError(
    InvalidListenerProfileProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileJSONError,
):
    """
    An error that is raised when the listener profile project manifest file is not a valid JSON
    file.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class InvalidListenerProfileProjectManifestFileSchemaError(
    InvalidListenerProfileProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """
    An error that is raised when the listener profile project manifest file does not conform to
    the expected JSON schema.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        json_schema_error_message: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidListenerProfileProjectPyProjectFileError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid `pyproject.toml`
    file.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PY_PROJECT_FILE_ERROR"


class InvalidListenerProfileProjectPyProjectFileTOMLError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """
    An error that is raised when the `pyproject.toml` file is not a valid TOML file
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PY_PROJECT_FILE_TOML_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class InvalidListenerProfileProjectPyProjectFileDependencyError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """
    An error that is raised when the `pyproject.toml` file contains invalid dependency
    entries.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PY_PROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidListenerProfileProjectFolderStructureError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectFolderStructureError,
):
    """
    Base exception for all errors that occur due to the listener profile being loaded having an
    invalid listener profile project folder structure.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_FOLDER_STRUCTURE_ERROR"


class ListenerProfileProjectManifestFileNotFoundError(
    InvalidListenerProfileProjectFolderStructureError,
    comp_svc_excs.ComponentProjectManifestFileNotFoundError,
):
    """
    An error that is raised when the listener profile project manifest file is not found in the
    listener profile project folder.
    """

    code = "LISTENER_PROFILE_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class ListenerProfileProjectListenerProfileFileNotFoundError(
    InvalidListenerProfileProjectFolderStructureError,
    comp_svc_excs.ComponentProjectComponentFileNotFoundError,
):
    """
    An error that is raised when the listener profile file specified in the manifest is not
    found in the listener profile project folder.
    """

    code = "LISTENER_PROFILE_PROJECT_LISTENER_PROFILE_FILE_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        listener_profile_file: str,
    ):
        super().__init__(
            component_file=listener_profile_file,
            component_project_folder=listener_profile_project_folder,
        )


class InvalidListenerProfileProjectImplementationError(
    ListenerProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectImplementationError,
):
    """
    Base exception for all errors that occur due to the listener profile project not implementing
    the required interface for the listener profile.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_IMPLEMENTATION_ERROR"


class ListenerProfileProjectSymbolNotFoundError(
    InvalidListenerProfileProjectImplementationError,
    comp_svc_excs.ComponentProjectSymbolNotFoundError,
):
    """
    An error that is raised when the listener profile symbol name specified in the manifest is not
    found in the listener profile file.
    """

    code = "LISTENER_PROFILE_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        symbol_name: str,
        listener_profile_file: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            symbol_name=symbol_name,
            component_file=listener_profile_file,
        )


class ListenerProfileProjectInterfaceError(
    InvalidListenerProfileProjectImplementationError,
    comp_svc_excs.ComponentProjectInterfaceError,
):
    """
    An error that is raised when the listener profile class does not implement the required
    interface for the listener profile.
    """

    code = "LISTENER_PROFILE_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        listener_profile_symbol: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            component_symbol=listener_profile_symbol,
        )


class InternalListenerProfileProjectError(
    InvalidListenerProfileProjectImplementationError,
    comp_svc_excs.InternalComponentProjectError,
):
    """
    An error that is raised when an unhandled exception from within the listener profile is
    raised while loading a listener profile project.
    """

    code = "INTERNAL_LISTENER_PROFILE_PROJECT_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatibleListenerProfileFrameworkVersionError(
    ListenerProfileLoadingError,
    comp_svc_excs.IncompatibleComponentFrameworkVersionError,
):
    """
    An error that is raised when a listener profile is incompatible with the current framework
    version.
    """

    code = "INCOMPATIBLE_LISTENER_PROFILE_FRAMEWORK_VERSION_ERROR"

    def __init__(
        self,
        listener_profile_str: str,
        required_version: str,
        current_version: str,
    ):
        super().__init__(
            component_str=listener_profile_str,
            required_version=required_version,
            current_version=current_version,
        )


class ListenerProfileAlreadyRegisteredError(
    ListenerProfileLoadingError,
    comp_svc_excs.ComponentAlreadyRegisteredError,
):
    """
    An error that is raised when a listener profile with the same ID is already registered in the
    listener profiles service.
    """

    code = "LISTENER_PROFILE_ALREADY_REGISTERED_ERROR"

    def __init__(self, listener_profile_str: str, listener_profile_id: str):
        super().__init__(
            component_str=listener_profile_str,
            component_id=listener_profile_id,
        )


class DuplicateListenerProfileLabelError(
    ListenerProfileLoadingError,
    comp_svc_excs.DuplicateComponentLabelError,
):
    """
    An error that is raised when a listener profile with the same `label` as the listener profile being
    registered has already been registered with the listener profiles service.
    """

    code = "DUPLICATE_LISTENER_PROFILE_LABEL_ERROR"

    def __init__(self, listener_profile_str: str, label: str):
        super().__init__(
            component_str=listener_profile_str,
            label=label,
        )


class ListenerProfileDependencyError(
    ListenerProfilesServiceError,
    comp_svc_excs.ComponentDependencyError,
):
    """
    Base exception for all errors that occur during the resolution of a plugin's
    dependencies.
    """

    code = "LISTENER_PROFILE_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "listener profile"


class ThirdPartyDependencyNotFoundError(
    ListenerProfileDependencyError,
    comp_svc_excs.ThirdPartyDependencyNotFoundError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is not
    installed.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(
    ListenerProfileDependencyError,
    comp_svc_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is
    incompatible with the plugin.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(
    ListenerProfileDependencyError,
    comp_svc_excs.ComponentDependencyNotFoundError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is not
    installed.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_str: str,
        missing_dependency: str,
    ):
        super().__init__(
            component_str=listener_profile_str,
            missing_dependency=missing_dependency,
        )


class IncompatibleComponentDependencyVersionError(
    ListenerProfileDependencyError,
    comp_svc_excs.IncompatibleComponentDependencyVersionError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is
    incompatible with the plugin.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        listener_profile_str: str,
        incompatible_dependency: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_str=listener_profile_str,
            incompatible_dependency=incompatible_dependency,
            required_version=required_version,
            installed_version=installed_version,
        )


class ListenerProfileDependsOnInvalidComponentDependencyError(
    ListenerProfileDependencyError,
    comp_svc_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """
    An error that is raised when a plugin depends on another plugin dependency that
    itself has invalid dependencies.
    """

    code = "LISTENER_PROFILE_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"

    def __init__(
        self,
        listener_profile_str: str,
        invalid_dependency: str,
    ):
        super().__init__(
            component_str=listener_profile_str,
            invalid_dependency=invalid_dependency,
        )


class ComponentDependencyNotRunningError(
    ListenerProfileDependencyError,
    comp_svc_excs.ComponentDependencyNotRunningError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is present but
    not currently running.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"

    def __init__(
        self,
        listener_profile_str: str,
        not_running_dependency: str,
    ):
        super().__init__(
            component_str=listener_profile_str,
            not_running_dependency=not_running_dependency,
        )


# class ListenerProfileLoadError(ListenerProfilesServiceError):
#     pass
#
#
# class InvalidListenerProjectManifestFileError(ListenerProfileLoadError):
#     pass
#
#
# class InvalidListenerProjectManifestFileJSONError(
#     InvalidListenerProjectManifestFileError,
# ):
#     def __init__(self, listener_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the listener project at '{listener_project_folder}'. "
#                 f"The listener project manifest file in the listener project folder is "
#                 f"not a valid JSON file."
#             ),
#         )
#
#
# class InvalidListenerProjectManifestFileSchemaError(
#     InvalidListenerProjectManifestFileError,
# ):
#     def __init__(self, listener_project_folder: str, json_schema_error_message: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the listener project at '{listener_project_folder}'. "
#                 f"The listener project manifest file in the listener project folder "
#                 f"failed JSON schema validation: {json_schema_error_message}"
#             ),
#         )
#
#
# class InvalidListenerProjectFolderStructureError(ListenerProfileLoadError):
#     pass
#
#
# class ListenerProjectManifestFileNotFoundError(
#     InvalidListenerProjectFolderStructureError,
# ):
#     def __init__(self, listener_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the listener project at '{listener_project_folder}'. "
#                 f"The listener project manifest file was not found in the listener "
#                 f"project folder."
#             ),
#         )
#
#
# class ListenerProjectListenerFileNotFoundError(
#     InvalidListenerProjectFolderStructureError,
# ):
#     def __init__(self, listener_file: str, listener_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the listener project at "
#                 f"'{listener_project_folder}'. The listener file '{listener_file}' "
#                 "specified in the listener project's manifest file was not found."
#             ),
#         )
#
#
# class ListenerProjectListenerTemplateFileNotFoundError(
#     InvalidListenerProjectFolderStructureError,
# ):
#     def __init__(self, listener_template_file: str, listener_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the listener project at "
#                 f"'{listener_project_folder}'. The listener template file "
#                 f"'{listener_template_file}' specified in the listener project's "
#                 f"manifest file was not found."
#             ),
#         )
#
#
# class ListenerProjectListenerTypeFileNotFoundError(
#     InvalidListenerProjectFolderStructureError,
# ):
#     def __init__(self, listener_type_file: str, listener_project_folder: str):
#         super().__init__(
#             f"Failed to load the listener project at '{listener_project_folder}'. The "
#             f"listener type file '{listener_type_file}' specified in the listener "
#             f"project's manifest file was not found.",
#         )
#
#
# class InvalidListenerProjectImplementationError(ListenerProfileLoadError):
#     pass
#
#
# class ListenerProjectInterfaceError(InvalidListenerProjectImplementationError):
#     def __init__(
#         self,
#         listener_project_file_type: Literal[
#             "listener",
#             "listener template",
#             "listener type",
#         ],
#         listener_project_folder: str,
#         listener_project_symbol: str,
#     ):
#         super().__init__(
#             f"Failed to load the listener project at '{listener_project_folder}'. "
#             f"The {listener_project_file_type} in the listener project does not "
#             f"implement the required interface for its defined symbol "
#             f"'{listener_project_symbol}'.",
#         )
#
#
# class ListenerProjectSymbolNotFoundError(InvalidListenerProjectImplementationError):
#     def __init__(
#         self,
#         symbol_name: str,
#         listener_project_file: str,
#         listener_project_folder: str,
#         listener_project_file_type: Literal[
#             "listener",
#             "listener template",
#             "listener type",
#         ],
#     ):
#         super().__init__(
#             f"Failed to load listener project at '{listener_project_folder}'. The "
#             f"symbol name '{symbol_name}' specified in the listener project's manifest "
#             f"file was not found in the {listener_project_file_type} file "
#             f"'{listener_project_file}'.",
#         )
#
#
# class InternalListenerProjectError(InvalidListenerProjectImplementationError):
#     def __init__(
#         self,
#         listener_project_file_type: Literal[
#             "listener",
#             "listener template",
#             "listener type",
#         ],
#         listener_project_folder: str,
#         error_message: str,
#     ):
#         super().__init__(
#             f"Failed to load listener project at '{listener_project_folder}'. An "
#             f"exception occurred while loading the "
#             f"{listener_project_file_type}: {error_message}",
#         )
