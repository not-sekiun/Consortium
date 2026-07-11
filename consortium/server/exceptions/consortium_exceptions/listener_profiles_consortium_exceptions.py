"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`ListenerProfilesError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfilesError]
        - [`ListenerProfilesServiceError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfilesServiceError]
            - [`ListenerProfileNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileNotFoundError]
            - [`ListenerProfileLoadingError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileLoadingError]
                - [`InvalidListenerProfileProjectManifestFileError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectManifestFileError]
                    - [`InvalidListenerProfileProjectManifestFileJSONError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectManifestFileJSONError]
                    - [`InvalidListenerProfileProjectManifestFileSchemaError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectManifestFileSchemaError]
                - [`InvalidListenerProfileProjectPyProjectFileError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectPyProjectFileError]
                - [`InvalidListenerProfileProjectPyProjectFileTOMLError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectPyProjectFileTOMLError]
                - [`InvalidListenerProfileProjectPyProjectFileDependencyError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectPyProjectFileDependencyError]
                - [`InvalidListenerProfileProjectFolderStructureError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectFolderStructureError]
                    - [`ListenerProfileProjectManifestFileNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileProjectManifestFileNotFoundError]
                    - [`ListenerProfileProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileProjectEntryPointModuleNotFoundError]
                - [`InvalidListenerProfileProjectImplementationError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InvalidListenerProfileProjectImplementationError]
                    - [`ListenerProfileProjectSymbolNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileProjectSymbolNotFoundError]
                    - [`ListenerProfileProjectInterfaceError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileProjectInterfaceError]
                    - [`InternalListenerProfileProjectError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.InternalListenerProfileProjectError]
                - [`IncompatibleListenerProfileFrameworkVersionError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.IncompatibleListenerProfileFrameworkVersionError]
                - [`ListenerProfileAlreadyRegisteredError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileAlreadyRegisteredError]
                - [`DuplicateListenerProfileLabelError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.DuplicateListenerProfileLabelError]
            - [`ListenerProfileDependencyError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileDependencyError]
                - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ThirdPartyDependencyNotFoundError]
                - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.IncompatibleThirdPartyDependencyVersionError]
                - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ComponentDependencyNotFoundError]
                - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.IncompatibleComponentDependencyVersionError]
                - [`ListenerProfileDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ListenerProfileDependsOnInvalidComponentDependencyError]
                - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.consortium_exceptions.listener_profiles_consortium_exceptions.ComponentDependencyNotRunningError]
"""

from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class ListenerProfilesError(BaseConsortiumError):
    """Base exception for all listener profiles related errors.

    All exceptions that inherit from `ListenerProfilesError` define, `code`, `message`, and
    `detail` attributes. For brevity, `message` and `detail` are omitted within
    the documentation here.

    Attributes:
        code: A **stable, machine-readable identifier** for the specific type of
            error that occurred.
        message: A human-readable message that describes the error.
        detail: Any JSON-serializable data structure holding **structured, raw data**
            relevant to the error.
    """

    code = "LISTENER_PROFILES_ERROR"


class ListenerProfilesServiceError(ListenerProfilesError):
    """Base exception for all errors that occur within the listener profiles service."""

    code = "LISTENER_PROFILES_SERVICE_ERROR"


class ListenerProfileNotFoundError(
    ListenerProfilesServiceError,
    comp_excs.ComponentNotFoundError,
):
    """Raised when the requested listener profile with the provided listener profile ID was not
    found in the listener profiles service.
    """

    code = "LISTENER_PROFILE_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "listener profile"

    def __init__(self, listener_profile_id: str):
        super().__init__(component_id=listener_profile_id)


class ListenerProfileLoadingError(
    ListenerProfilesServiceError,
    comp_excs.ComponentLoadingError,
):
    """Base exception for all errors that occur during the loading of a listener profile."""

    code = "LISTENER_PROFILE_LOADING_ERROR"

    _COMPONENT_TYPE = "listener profile"


class InvalidListenerProfileProjectManifestFileError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentProjectManifestFileError,
):
    """Base exception for all errors that occur due to an invalid listener profile project
    manifest `manifest.json` file during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_ERROR"


class InvalidListenerProfileProjectManifestFileJSONError(
    InvalidListenerProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileJSONError,
):
    """Raised when the listener profile project manifest file is not valid JSON during
    listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class InvalidListenerProfileProjectManifestFileSchemaError(
    InvalidListenerProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the listener profile project manifest file does not conform to the expected
    JSON schema during listener profile loading.
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
    comp_excs.InvalidComponentProjectPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidListenerProfileProjectPyProjectFileTOMLError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during listener profile
    loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PYPROJECT_FILE_TOML_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class InvalidListenerProfileProjectPyProjectFileDependencyError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

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
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid listener profile project
    folder structure during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_FOLDER_STRUCTURE_ERROR"


class ListenerProfileProjectManifestFileNotFoundError(
    InvalidListenerProfileProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the listener profile project manifest file is not found in the listener
    profile project folder during listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, listener_profile_project_folder: str):
        super().__init__(component_project_folder=listener_profile_project_folder)


class ListenerProfileProjectEntryPointModuleNotFoundError(
    InvalidListenerProfileProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the listener profile entry point module specified in the manifest is not
    found in the listener profile project folder during listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            entry_point_module=entry_point_module,
        )


class InvalidListenerProfileProjectImplementationError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentProjectImplementationError,
):
    """Base exception for all errors that occur due to the listener profile project not
    implementing the required interface during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_IMPLEMENTATION_ERROR"


class ListenerProfileProjectSymbolNotFoundError(
    InvalidListenerProfileProjectImplementationError,
    comp_excs.ComponentProjectSymbolNotFoundError,
):
    """Raised when the listener profile symbol name specified in the manifest is not found in
    the listener profile entry point module during listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class ListenerProfileProjectInterfaceError(
    InvalidListenerProfileProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the listener profile class does not implement the required interface during
    listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        listener_profile_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_project_folder=listener_profile_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalListenerProfileProjectError(
    InvalidListenerProfileProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the listener profile is raised during
    listener profile loading.
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
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when a listener profile's required framework version is incompatible with the
    current framework version during listener profile loading.
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
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when a listener profile with the same ID is already registered in the listener
    profiles service during listener profile loading.
    """

    code = "LISTENER_PROFILE_ALREADY_REGISTERED_ERROR"

    def __init__(self, listener_profile_str: str, listener_profile_id: str):
        super().__init__(
            component_str=listener_profile_str,
            component_id=listener_profile_id,
        )


class DuplicateListenerProfileLabelError(
    ListenerProfileLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the listener profile's definition is already in use by
    another listener profile during listener profile loading.
    """

    code = "DUPLICATE_LISTENER_PROFILE_LABEL_ERROR"

    def __init__(self, listener_profile_str: str, label: str):
        super().__init__(
            component_str=listener_profile_str,
            label=label,
        )


class ListenerProfileDependencyError(
    ListenerProfilesServiceError,
    comp_excs.ComponentDependencyError,
):
    """Base exception for all errors that occur during the resolution of listener profile's
    dependencies.
    """

    code = "LISTENER_PROFILE_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "listener profile"


class ThirdPartyDependencyNotFoundError(
    ListenerProfileDependencyError,
    comp_excs.ThirdPartyDependencyNotFoundError,
):
    """Raised when a third-party dependency required by a listener profile is not installed
    during listener profile dependency resolution.
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
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the listener profile during listener profile dependency resolution.
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
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a component dependency required by the listener profile is not found in the
    components service during listener profile dependency resolution.
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
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a component dependency's version is incompatible with the version required
    by the listener profile during listener profile dependency resolution.
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
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when a listener profile depends on another component dependency that itself has
    invalid dependencies during listener profile dependency resolution.
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
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a component dependency required by the listener profile is present but not
    currently running during listener profile dependency resolution.
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
