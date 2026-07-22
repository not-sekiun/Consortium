"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ListenerProfilesServiceError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfilesServiceError]
        - [`ListenerProfileNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileNotFoundError]
        - [`ListenerProfileLoadingError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileLoadingError]
            - [`InvalidListenerProfileManifestFileError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileManifestFileError]
                - [`InvalidListenerProfileManifestFileJSONError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileManifestFileJSONError]
                - [`InvalidListenerProfileManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileManifestFileSchemaError]
            - [`InvalidListenerProfilePyProjectFileError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfilePyProjectFileError]
            - [`InvalidListenerProfilePyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfilePyProjectFileTOMLError]
            - [`InvalidListenerProfilePyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfilePyProjectFileDependencyError]
            - [`InvalidListenerProfileDirectoryStructureError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileDirectoryStructureError]
                - [`ListenerProfileManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileManifestFileNotFoundError]
                - [`ListenerProfileEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileEntryPointModuleNotFoundError]
            - [`InvalidListenerProfileImplementationError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InvalidListenerProfileImplementationError]
                - [`ListenerProfileSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileSymbolNotFoundError]
                - [`ListenerProfileInterfaceError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.ListenerProfileInterfaceError]
                - [`InternalListenerProfileError`][consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions.InternalListenerProfileError]
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


class InvalidListenerProfileManifestFileError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentManifestFileError,
):
    """Base exception for all errors that occur due to an invalid listener profile
    manifest file during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_MANIFEST_FILE_ERROR"


class InvalidListenerProfileManifestFileJSONError(
    InvalidListenerProfileManifestFileError,
    comp_excs.InvalidComponentManifestFileJSONError,
):
    """Raised when the listener profile manifest file is not valid JSON during
    listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_MANIFEST_FILE_JSON_ERROR"


class InvalidListenerProfileManifestFileSchemaError(
    InvalidListenerProfileManifestFileError,
    comp_excs.InvalidComponentManifestFileSchemaError,
):
    """Raised when the listener profile manifest file does not conform to the expected
    JSON schema during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_MANIFEST_FILE_SCHEMA_ERROR"


class InvalidListenerProfilePyProjectFileError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PYPROJECT_FILE_ERROR"


class InvalidListenerProfilePyProjectFileTOMLError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during listener profile
    loading.
    """

    code = "INVALID_LISTENER_PROFILE_PYPROJECT_FILE_TOML_ERROR"


class InvalidListenerProfilePyProjectFileDependencyError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidListenerProfileDirectoryStructureError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentDirectoryStructureError,
):
    """Base exception for all errors that occur due to an invalid listener profile
    directory structure during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_DIRECTORY_STRUCTURE_ERROR"


class ListenerProfileManifestFileNotFoundError(
    InvalidListenerProfileDirectoryStructureError,
    comp_excs.ComponentManifestFileNotFoundError,
):
    """Raised when the listener profile manifest file is not found in the listener
    profile directory during listener profile loading.
    """

    code = "LISTENER_PROFILE_MANIFEST_FILE_NOT_FOUND_ERROR"


class ListenerProfileEntryPointModuleNotFoundError(
    InvalidListenerProfileDirectoryStructureError,
    comp_excs.ComponentEntryPointModuleNotFoundError,
):
    """Raised when the listener profile entry point module specified in the manifest
    file is not found in the listener profile directory during listener profile loading.
    """

    code = "LISTENER_PROFILE_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


class InvalidListenerProfileImplementationError(
    ListenerProfileLoadingError,
    comp_excs.InvalidComponentImplementationError,
):
    """Base exception for all errors that occur due to the listener profile not
    implementing the required interface during listener profile loading.
    """

    code = "INVALID_LISTENER_PROFILE_IMPLEMENTATION_ERROR"


class ListenerProfileSymbolNotFoundError(
    InvalidListenerProfileImplementationError,
    comp_excs.ComponentSymbolNotFoundError,
):
    """Raised when the listener profile symbol name specified in the manifest file is
    not found in the listener profile entry point module during listener profile loading.
    """

    code = "LISTENER_PROFILE_SYMBOL_NOT_FOUND_ERROR"


class ListenerProfileInterfaceError(
    InvalidListenerProfileImplementationError,
    comp_excs.ComponentInterfaceError,
):
    """Raised when the listener profile class does not implement the required interface during
    listener profile loading.
    """

    code = "LISTENER_PROFILE_INTERFACE_ERROR"


class InternalListenerProfileError(
    InvalidListenerProfileImplementationError,
    comp_excs.InternalComponentError,
):
    """Raised when an unhandled exception from within the listener profile is raised during
    listener profile loading.
    """

    code = "INTERNAL_LISTENER_PROFILE_ERROR"


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
