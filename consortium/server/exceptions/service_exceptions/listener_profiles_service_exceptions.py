"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ListenerProfilesServiceError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfilesServiceError]
        - [`ListenerProfileNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileNotFoundError]
        - [`ListenerProfileLoadingError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileLoadingError]
            - [`InvalidListenerProfileProjectManifestFileError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectManifestFileError]
                - [`InvalidListenerProfileProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectManifestFileJSONError]
                - [`InvalidListenerProfileProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectManifestFileSchemaError]
            - [`InvalidListenerProfileProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectPyProjectFileError]
            - [`InvalidListenerProfileProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectPyProjectFileTOMLError]
            - [`InvalidListenerProfileProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectPyProjectFileDependencyError]
            - [`InvalidListenerProfileProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectFolderStructureError]
                - [`ListenerProfileProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileProjectManifestFileNotFoundError]
                - [`ListenerProfileProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileProjectEntryPointModuleNotFoundError]
            - [`InvalidListenerProfileProjectImplementationError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileProjectImplementationError]
                - [`ListenerProfileProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileProjectSymbolNotFoundError]
                - [`ListenerProfileProjectInterfaceError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileProjectInterfaceError]
                - [`InternalListenerProfileProjectError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InternalListenerProfileProjectError]
            - [`IncompatibleListenerProfileFrameworkVersionError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.IncompatibleListenerProfileFrameworkVersionError]
            - [`ListenerProfileAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileAlreadyRegisteredError]
            - [`DuplicateListenerProfileLabelError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.DuplicateListenerProfileLabelError]
        - [`ListenerProfileDependencyError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ComponentDependencyNotFoundError]
            - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.IncompatibleComponentDependencyVersionError]
            - [`ListenerProfileDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileDependsOnInvalidComponentDependencyError]
            - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ComponentDependencyNotRunningError]

The loading, dependency, and registry exceptions below carry no `__init__` of their own: they
are constructed by the shared component loader/registry pipeline with the generic component
keyword arguments (`component_directory`, `component_str`, `component_id`, ...) inherited from
their `components_service_exceptions` base.
"""

from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class ListenerProfilesServiceError(BaseServiceError):
    """Base exception for all errors that occur within the listener profiles service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

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


class InvalidListenerProfileProjectManifestFileSchemaError(
    InvalidListenerProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the listener profile project manifest file does not conform to the expected
    JSON schema during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"


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


class InvalidListenerProfileProjectPyProjectFileDependencyError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"


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


class ListenerProfileProjectEntryPointModuleNotFoundError(
    InvalidListenerProfileProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the listener profile entry point module specified in the manifest is not
    found in the listener profile project folder during listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


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


class ListenerProfileProjectInterfaceError(
    InvalidListenerProfileProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the listener profile class does not implement the required interface during
    listener profile loading.
    """

    code = "LISTENER_PROFILE_PROJECT_INTERFACE_ERROR"


class InternalListenerProfileProjectError(
    InvalidListenerProfileProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the listener profile is raised during
    listener profile loading.
    """

    code = "INTERNAL_LISTENER_PROFILE_PROJECT_ERROR"


class IncompatibleListenerProfileFrameworkVersionError(
    ListenerProfileLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when a listener profile's required framework version is incompatible with the
    current framework version during listener profile loading.
    """

    code = "INCOMPATIBLE_LISTENER_PROFILE_FRAMEWORK_VERSION_ERROR"


class ListenerProfileAlreadyRegisteredError(
    ListenerProfileLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when a listener profile with the same ID is already registered in the listener
    profiles service during listener profile loading.
    """

    code = "LISTENER_PROFILE_ALREADY_REGISTERED_ERROR"


class DuplicateListenerProfileLabelError(
    ListenerProfileLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the listener profile's definition is already in use by
    another listener profile during listener profile loading.
    """

    code = "DUPLICATE_LISTENER_PROFILE_LABEL_ERROR"


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


class IncompatibleThirdPartyDependencyVersionError(
    ListenerProfileDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the listener profile during listener profile dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"


class ComponentDependencyNotFoundError(
    ListenerProfileDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a component dependency required by the listener profile is not found in the
    components service during listener profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleComponentDependencyVersionError(
    ListenerProfileDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a component dependency's version is incompatible with the version required
    by the listener profile during listener profile dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"


class ListenerProfileDependsOnInvalidComponentDependencyError(
    ListenerProfileDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when a listener profile depends on another component dependency that itself has
    invalid dependencies during listener profile dependency resolution.
    """

    code = "LISTENER_PROFILE_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"


class ComponentDependencyNotRunningError(
    ListenerProfileDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a component dependency required by the listener profile is present but not
    currently running during listener profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"
