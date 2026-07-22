"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AgentProfilesServiceError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfilesServiceError]
        - [`AgentProfileNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileNotFoundError]
        - [`AgentProfileLoadingError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileLoadingError]
            - [`InvalidAgentProfileProjectManifestFileError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectManifestFileError]
                - [`InvalidAgentProfileProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectManifestFileJSONError]
                - [`InvalidAgentProfileProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectManifestFileSchemaError]
            - [`InvalidAgentProfileProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectPyProjectFileError]
            - [`InvalidAgentProfileProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectPyProjectFileTOMLError]
            - [`InvalidAgentProfileProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectPyProjectFileDependencyError]
            - [`InvalidAgentProfileProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectFolderStructureError]
                - [`AgentProfileProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileProjectManifestFileNotFoundError]
                - [`AgentProfileProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileProjectEntryPointModuleNotFoundError]
            - [`InvalidAgentProfileProjectImplementationError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileProjectImplementationError]
                - [`AgentProfileProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileProjectSymbolNotFoundError]
                - [`AgentProfileProjectInterfaceError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileProjectInterfaceError]
                - [`InternalAgentProfileProjectError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InternalAgentProfileProjectError]
            - [`IncompatibleAgentProfileFrameworkVersionError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.IncompatibleAgentProfileFrameworkVersionError]
            - [`AgentProfileAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileAlreadyRegisteredError]
            - [`DuplicateAgentProfileLabelError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.DuplicateAgentProfileLabelError]
        - [`AgentProfileDependencyError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.ComponentDependencyNotFoundError]
            - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.IncompatibleComponentDependencyVersionError]
            - [`AgentProfileDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileDependsOnInvalidComponentDependencyError]
            - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.ComponentDependencyNotRunningError]

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


class AgentProfilesServiceError(BaseServiceError):
    """Base exception for all errors that occur within the agent profiles service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "AGENT_PROFILES_SERVICE_ERROR"


class AgentProfileNotFoundError(
    AgentProfilesServiceError,
    comp_excs.ComponentNotFoundError,
):
    """Raised when the requested agent profile with the provided agent profile ID was not
    found in the agent profiles service.
    """

    code = "AGENT_PROFILE_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "agent profile"


class AgentProfileLoadingError(
    AgentProfilesServiceError,
    comp_excs.ComponentLoadingError,
):
    """Base exception for all errors that occur during the loading of an agent profile."""

    code = "AGENT_PROFILE_LOADING_ERROR"

    _COMPONENT_TYPE = "agent profile"


class InvalidAgentProfileProjectManifestFileError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectManifestFileError,
):
    """Base exception for all errors that occur due to an invalid agent profile project
    manifest `manifest.json` file during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_ERROR"


class InvalidAgentProfileProjectManifestFileJSONError(
    InvalidAgentProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileJSONError,
):
    """Raised when the agent profile project manifest file is not valid JSON during agent
    profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_JSON_ERROR"


class InvalidAgentProfileProjectManifestFileSchemaError(
    InvalidAgentProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the agent profile project manifest file does not conform to the expected
    JSON schema during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"


class InvalidAgentProfileProjectPyProjectFileError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidAgentProfileProjectPyProjectFileTOMLError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during agent profile
    loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PYPROJECT_FILE_TOML_ERROR"


class InvalidAgentProfileProjectPyProjectFileDependencyError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidAgentProfileProjectFolderStructureError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid agent profile root
    directory structure during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_FOLDER_STRUCTURE_ERROR"


class AgentProfileProjectManifestFileNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the agent profile project manifest file is not found in the agent profile
    root directory during agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"


class AgentProfileProjectEntryPointModuleNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the agent profile entry point module specified in the manifest is not
    found in the agent profile root directory during agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


class InvalidAgentProfileProjectImplementationError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectImplementationError,
):
    """Base exception for all errors that occur due to the agent profile project not
    implementing the required interface during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_IMPLEMENTATION_ERROR"


class AgentProfileProjectSymbolNotFoundError(
    InvalidAgentProfileProjectImplementationError,
    comp_excs.ComponentProjectSymbolNotFoundError,
):
    """Raised when the agent profile symbol name specified in the manifest is not found in
    the agent profile entry point module during agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_SYMBOL_NOT_FOUND_ERROR"


class AgentProfileProjectInterfaceError(
    InvalidAgentProfileProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the agent profile class does not implement the required interface during
    agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_INTERFACE_ERROR"


class InternalAgentProfileProjectError(
    InvalidAgentProfileProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the agent profile is raised during
    agent profile loading.
    """

    code = "INTERNAL_AGENT_PROFILE_PROJECT_ERROR"


class IncompatibleAgentProfileFrameworkVersionError(
    AgentProfileLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when an agent profile's required framework version is incompatible with the
    current framework version during agent profile loading.
    """

    code = "INCOMPATIBLE_AGENT_PROFILE_FRAMEWORK_VERSION_ERROR"


class AgentProfileAlreadyRegisteredError(
    AgentProfileLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when an agent profile with the same ID is already registered in the agent
    profiles service during agent profile loading.
    """

    code = "AGENT_PROFILE_ALREADY_REGISTERED_ERROR"


class DuplicateAgentProfileLabelError(
    AgentProfileLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the agent profile's definition is already in use by
    another agent profile during agent profile loading.
    """

    code = "DUPLICATE_AGENT_PROFILE_LABEL_ERROR"


class AgentProfileDependencyError(
    AgentProfilesServiceError,
    comp_excs.ComponentDependencyError,
):
    """Base exception for all errors that occur during the resolution of agent profile
    dependencies.
    """

    code = "AGENT_PROFILE_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "agent profile"


class ThirdPartyDependencyNotFoundError(
    AgentProfileDependencyError,
    comp_excs.ThirdPartyDependencyNotFoundError,
):
    """Raised when a third-party dependency required by an agent profile is not installed
    during agent profile dependency resolution.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleThirdPartyDependencyVersionError(
    AgentProfileDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the agent profile during agent profile dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"


class ComponentDependencyNotFoundError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a component dependency required by the agent profile is not found in the
    components service during agent profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleComponentDependencyVersionError(
    AgentProfileDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a component dependency's version is incompatible with the version required
    by the agent profile during agent profile dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"


class AgentProfileDependsOnInvalidComponentDependencyError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when an agent profile depends on another component dependency that itself has
    invalid dependencies during agent profile dependency resolution.
    """

    code = "AGENT_PROFILE_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"


class ComponentDependencyNotRunningError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a component dependency required by the agent profile is present but not
    currently running during agent profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"
