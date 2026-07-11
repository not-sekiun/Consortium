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

    def __init__(self, agent_profile_id: str):
        super().__init__(component_id=agent_profile_id)


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

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class InvalidAgentProfileProjectManifestFileSchemaError(
    InvalidAgentProfileProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the agent profile project manifest file does not conform to the expected
    JSON schema during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        json_schema_error_message: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


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

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class InvalidAgentProfileProjectPyProjectFileDependencyError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidAgentProfileProjectFolderStructureError(
    AgentProfileLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid agent profile project
    folder structure during agent profile loading.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_FOLDER_STRUCTURE_ERROR"


class AgentProfileProjectManifestFileNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the agent profile project manifest file is not found in the agent profile
    project folder during agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class AgentProfileProjectEntryPointModuleNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the agent profile entry point module specified in the manifest is not
    found in the agent profile project folder during agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            entry_point_module=entry_point_module,
        )


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

    def __init__(
        self,
        agent_profile_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class AgentProfileProjectInterfaceError(
    InvalidAgentProfileProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the agent profile class does not implement the required interface during
    agent profile loading.
    """

    code = "AGENT_PROFILE_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalAgentProfileProjectError(
    InvalidAgentProfileProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the agent profile is raised during
    agent profile loading.
    """

    code = "INTERNAL_AGENT_PROFILE_PROJECT_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatibleAgentProfileFrameworkVersionError(
    AgentProfileLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when an agent profile's required framework version is incompatible with the
    current framework version during agent profile loading.
    """

    code = "INCOMPATIBLE_AGENT_PROFILE_FRAMEWORK_VERSION_ERROR"

    def __init__(
        self,
        agent_profile_str: str,
        required_version: str,
        current_version: str,
    ):
        super().__init__(
            component_str=agent_profile_str,
            required_version=required_version,
            current_version=current_version,
        )


class AgentProfileAlreadyRegisteredError(
    AgentProfileLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when an agent profile with the same ID is already registered in the agent
    profiles service during agent profile loading.
    """

    code = "AGENT_PROFILE_ALREADY_REGISTERED_ERROR"

    def __init__(self, agent_profile_str: str, agent_profile_id: str):
        super().__init__(
            component_str=agent_profile_str,
            component_id=agent_profile_id,
        )


class DuplicateAgentProfileLabelError(
    AgentProfileLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the agent profile's definition is already in use by
    another agent profile during agent profile loading.
    """

    code = "DUPLICATE_AGENT_PROFILE_LABEL_ERROR"

    def __init__(self, agent_profile_str: str, label: str):
        super().__init__(
            component_str=agent_profile_str,
            label=label,
        )


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

    def __init__(
        self,
        agent_profile_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(
    AgentProfileDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the agent profile during agent profile dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when a component dependency required by the agent profile is not found in the
    components service during agent profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        agent_profile_str: str,
        missing_dependency: str,
    ):
        super().__init__(
            component_str=agent_profile_str,
            missing_dependency=missing_dependency,
        )


class IncompatibleComponentDependencyVersionError(
    AgentProfileDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when a component dependency's version is incompatible with the version required
    by the agent profile during agent profile dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        agent_profile_str: str,
        incompatible_dependency: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_str=agent_profile_str,
            incompatible_dependency=incompatible_dependency,
            required_version=required_version,
            installed_version=installed_version,
        )


class AgentProfileDependsOnInvalidComponentDependencyError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when an agent profile depends on another component dependency that itself has
    invalid dependencies during agent profile dependency resolution.
    """

    code = "AGENT_PROFILE_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"

    def __init__(
        self,
        agent_profile_str: str,
        invalid_dependency: str,
    ):
        super().__init__(
            component_str=agent_profile_str,
            invalid_dependency=invalid_dependency,
        )


class ComponentDependencyNotRunningError(
    AgentProfileDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when a component dependency required by the agent profile is present but not
    currently running during agent profile dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"

    def __init__(
        self,
        agent_profile_str: str,
        not_running_dependency: str,
    ):
        super().__init__(
            component_str=agent_profile_str,
            not_running_dependency=not_running_dependency,
        )
