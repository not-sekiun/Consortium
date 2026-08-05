"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`AgentProfilesServiceError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfilesServiceError]
        - [`AgentProfileNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileNotFoundError]
        - [`AgentProfileLoadingError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileLoadingError]
            - [`InvalidAgentProfileManifestFileError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileManifestFileError]
                - [`InvalidAgentProfileManifestFileJSONError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileManifestFileJSONError]
                - [`InvalidAgentProfileManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileManifestFileSchemaError]
            - [`InvalidAgentProfilePyProjectFileError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfilePyProjectFileError]
            - [`InvalidAgentProfilePyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfilePyProjectFileTOMLError]
            - [`InvalidAgentProfilePyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfilePyProjectFileDependencyError]
            - [`InvalidAgentProfileDirectoryStructureError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileDirectoryStructureError]
                - [`AgentProfileManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileManifestFileNotFoundError]
                - [`AgentProfileEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileEntryPointModuleNotFoundError]
            - [`InvalidAgentProfileImplementationError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InvalidAgentProfileImplementationError]
                - [`AgentProfileSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileSymbolNotFoundError]
                - [`AgentProfileInterfaceError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileInterfaceError]
                - [`InternalAgentProfileError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.InternalAgentProfileError]
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
        - [`AgentProfileDiscoveryFileSystemError`][consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions.AgentProfileDiscoveryFileSystemError]

The loading, dependency, and registry exceptions below carry no `__init__` of their own: they
are constructed by the shared component loader/registry pipeline with the generic component
keyword arguments (`component_directory`, `component_str`, `component_id`, ...) inherited from
their `components_service_exceptions` base. `AgentProfileDiscoveryFileSystemError` also carries
no `__init__` of its own: it inherits the `operation`/`path`/`underlying_error` constructor from
`ComponentDiscoveryFileSystemError` so it plugs directly into the shared
`wrap_filesystem_errors` helper.
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


class InvalidAgentProfileManifestFileError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentManifestFileError,
):
    """Base exception for all errors that occur due to an invalid agent profile
    manifest file during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_MANIFEST_FILE_ERROR"


class InvalidAgentProfileManifestFileJSONError(
    InvalidAgentProfileManifestFileError,
    comp_excs.InvalidComponentManifestFileJSONError,
):
    """Raised when the agent profile manifest file is not valid JSON during agent
    profile loading.
    """

    code = "INVALID_AGENT_PROFILE_MANIFEST_FILE_JSON_ERROR"


class InvalidAgentProfileManifestFileSchemaError(
    InvalidAgentProfileManifestFileError,
    comp_excs.InvalidComponentManifestFileSchemaError,
):
    """Raised when the agent profile manifest file does not conform to the expected
    JSON schema during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_MANIFEST_FILE_SCHEMA_ERROR"


class InvalidAgentProfilePyProjectFileError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PYPROJECT_FILE_ERROR"


class InvalidAgentProfilePyProjectFileTOMLError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during agent profile
    loading.
    """

    code = "INVALID_AGENT_PROFILE_PYPROJECT_FILE_TOML_ERROR"


class InvalidAgentProfilePyProjectFileDependencyError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidAgentProfileDirectoryStructureError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentDirectoryStructureError,
):
    """Base exception for all errors that occur due to an invalid agent profile
    directory structure during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_DIRECTORY_STRUCTURE_ERROR"


class AgentProfileManifestFileNotFoundError(
    InvalidAgentProfileDirectoryStructureError,
    comp_excs.ComponentManifestFileNotFoundError,
):
    """Raised when the agent profile manifest file is not found in the agent profile
    directory during agent profile loading.
    """

    code = "AGENT_PROFILE_MANIFEST_FILE_NOT_FOUND_ERROR"


class AgentProfileEntryPointModuleNotFoundError(
    InvalidAgentProfileDirectoryStructureError,
    comp_excs.ComponentEntryPointModuleNotFoundError,
):
    """Raised when the agent profile entry point module specified in the manifest file
    is not found in the agent profile directory during agent profile loading.
    """

    code = "AGENT_PROFILE_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


class InvalidAgentProfileImplementationError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentImplementationError,
):
    """Base exception for all errors that occur due to the agent profile not
    implementing the required interface during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_IMPLEMENTATION_ERROR"


class AgentProfileSymbolNotFoundError(
    InvalidAgentProfileImplementationError,
    comp_excs.ComponentSymbolNotFoundError,
):
    """Raised when the agent profile symbol name specified in the manifest file is not
    found in the agent profile entry point module during agent profile loading.
    """

    code = "AGENT_PROFILE_SYMBOL_NOT_FOUND_ERROR"


class AgentProfileInterfaceError(
    InvalidAgentProfileImplementationError,
    comp_excs.ComponentInterfaceError,
):
    """Raised when the agent profile class does not implement the required interface during
    agent profile loading.
    """

    code = "AGENT_PROFILE_INTERFACE_ERROR"


class InternalAgentProfileError(
    InvalidAgentProfileImplementationError,
    comp_excs.InternalComponentError,
):
    """Raised when an unhandled exception from within the agent profile is raised during
    agent profile loading.
    """

    code = "INTERNAL_AGENT_PROFILE_ERROR"


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


class AgentProfileDiscoveryFileSystemError(
    AgentProfilesServiceError,
    comp_excs.ComponentDiscoveryFileSystemError,
):
    """Raised when a recursive filesystem scan for agent profiles fails at the filesystem level."""

    code = "AGENT_PROFILE_DISCOVERY_FILE_SYSTEM_ERROR"
