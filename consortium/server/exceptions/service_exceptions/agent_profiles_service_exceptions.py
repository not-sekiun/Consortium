"""
Exception hierarchy for errors related to agent projects:

- BaseServiceException: Base class for all service-related exceptions.
  - AgentProfilesServiceError: Base class for all errors related to the agent
  profiles service.
    - AgentProfileNotFoundError: Raised when an agent profile is not found.
    - AgentProfileLoadError: Raised when an agent profile fails to load.
      - InvalidAgentProjectManifestFileError: Raised when the agent project
      manifest file is invalid.
        - AgentProjectManifestFileInvalidJSONError: Raised when the agent project
        manifest file is not a valid JSON file.
        - AgentProjectManifestFileSchemaError: Raised when the agent project
        manifest file does not conform to the expected schema.
      - InvalidAgentProjectFolderStructureError: Raised when the agent project
      folder structure is invalid.
        - AgentProjectManifestFileNotFoundError: Raised when the agent project
        manifest file is not found.
        - AgentProjectAgentGeneratorFileNotFoundError: Raised when the agent
        generator file specified in the manifest is not found.
        - AgentProjectAgentTemplateFileNotFoundError: Raised when the agent
        template file specified in the manifest is not found.
        - AgentProjectAgentTypeFileNotFoundError: Raised when the agent type
        file specified in the manifest is not found.
      - InvalidAgentProjectImplementationError: Raised when an agent project's
      implementation is invalid.
        - AgentProjectInterfaceError: Raised when a symbol (agent generator,
        agent template, or agent type) does not implement its respective interface.
        - AgentProjectSymbolNotFoundError: Raised when a symbol (agent generator,
        agent template, or agent type) is not found.
        - InternalAgentProjectError: Raised when an internal error occurs while
        handling an agent project.
"""

from consortium.server.exceptions.service_exceptions import (
    component_service_exceptions as comp_svc_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentProfilesServiceError(BaseServiceException):
    code = "AGENT_PROFILES_SERVICE_ERROR"


class AgentProfileNotFoundError(
    AgentProfilesServiceError,
    comp_svc_excs.ComponentNotFoundError,
):
    """
    An error that is raised when a agent profile is not found in the agent
    profiles service.
    """

    code = "AGENT_PROFILE_NOT_FOUND_ERROR"

    _COMPONENT_TYPE = "agent profile"

    def __init__(self, agent_profile_id: str):
        super().__init__(component_id=agent_profile_id)


class AgentProfileLoadingError(
    AgentProfilesServiceError,
    comp_svc_excs.ComponentLoadingError,
):
    """
    Base exception for all errors that occur during the loading of a agent profile.
    """

    code = "AGENT_PROFILE_LOADING_ERROR"

    _COMPONENT_TYPE = "agent profile"


class InvalidAgentProfileProjectManifestFileError(
    AgentProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectManifestFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid agent profile project
    manifest `manifest.json` file.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_ERROR"


class InvalidAgentProfileProjectManifestFileJSONError(
    InvalidAgentProfileProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileJSONError,
):
    """
    An error that is raised when the agent profile project manifest file is not a valid JSON
    file.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class InvalidAgentProfileProjectManifestFileSchemaError(
    InvalidAgentProfileProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """
    An error that is raised when the agent profile project manifest file does not conform to
    the expected JSON schema.
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
    comp_svc_excs.InvalidComponentProjectPyProjectFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid `pyproject.toml`
    file.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PY_PROJECT_FILE_ERROR"


class InvalidAgentProfileProjectPyProjectFileTOMLError(
    AgentProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """
    An error that is raised when the `pyproject.toml` file is not a valid TOML file
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PY_PROJECT_FILE_TOML_ERROR"

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class InvalidAgentProfileProjectPyProjectFileDependencyError(
    AgentProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """
    An error that is raised when the `pyproject.toml` file contains invalid dependency
    entries.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_PY_PROJECT_FILE_DEPENDENCY_ERROR"

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
    comp_svc_excs.InvalidComponentProjectFolderStructureError,
):
    """
    Base exception for all errors that occur due to the agent profile being loaded having an
    invalid agent profile project folder structure.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_FOLDER_STRUCTURE_ERROR"


class AgentProfileProjectManifestFileNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_svc_excs.ComponentProjectManifestFileNotFoundError,
):
    """
    An error that is raised when the agent profile project manifest file is not found in the
    agent profile project folder.
    """

    code = "AGENT_PROFILE_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, agent_profile_project_folder: str):
        super().__init__(component_project_folder=agent_profile_project_folder)


class AgentProfileProjectAgentProfileFileNotFoundError(
    InvalidAgentProfileProjectFolderStructureError,
    comp_svc_excs.ComponentProjectComponentFileNotFoundError,
):
    """
    An error that is raised when the agent profile file specified in the manifest is not
    found in the agent profile project folder.
    """

    code = "AGENT_PROFILE_PROJECT_AGENT_PROFILE_FILE_NOT_FOUND_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        agent_profile_file: str,
    ):
        super().__init__(
            component_file=agent_profile_file,
            component_project_folder=agent_profile_project_folder,
        )


class InvalidAgentProfileProjectImplementationError(
    AgentProfileLoadingError,
    comp_svc_excs.InvalidComponentProjectImplementationError,
):
    """
    Base exception for all errors that occur due to the agent profile project not implementing
    the required interface for the agent profile.
    """

    code = "INVALID_AGENT_PROFILE_PROJECT_IMPLEMENTATION_ERROR"


class AgentProfileProjectSymbolNotFoundError(
    InvalidAgentProfileProjectImplementationError,
    comp_svc_excs.ComponentProjectSymbolNotFoundError,
):
    """
    An error that is raised when the agent profile symbol name specified in the manifest is not
    found in the agent profile file.
    """

    code = "AGENT_PROFILE_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        symbol_name: str,
        agent_profile_file: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            symbol_name=symbol_name,
            component_file=agent_profile_file,
        )


class AgentProfileProjectInterfaceError(
    InvalidAgentProfileProjectImplementationError,
    comp_svc_excs.ComponentProjectInterfaceError,
):
    """
    An error that is raised when the agent profile class does not implement the required
    interface for the agent profile.
    """

    code = "AGENT_PROFILE_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        agent_profile_project_folder: str,
        agent_profile_symbol: str,
    ):
        super().__init__(
            component_project_folder=agent_profile_project_folder,
            component_symbol=agent_profile_symbol,
        )


class InternalAgentProfileProjectError(
    InvalidAgentProfileProjectImplementationError,
    comp_svc_excs.InternalComponentProjectError,
):
    """
    An error that is raised when an unhandled exception from within the agent profile is
    raised while loading a agent profile project.
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
    comp_svc_excs.IncompatibleComponentFrameworkVersionError,
):
    """
    An error that is raised when a agent profile is incompatible with the current framework
    version.
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
    comp_svc_excs.ComponentAlreadyRegisteredError,
):
    """
    An error that is raised when a agent profile with the same ID is already registered in the
    agent profiles service.
    """

    code = "AGENT_PROFILE_ALREADY_REGISTERED_ERROR"

    def __init__(self, agent_profile_str: str, agent_profile_id: str):
        super().__init__(
            component_str=agent_profile_str,
            component_id=agent_profile_id,
        )


class DuplicateAgentProfileLabelError(
    AgentProfileLoadingError,
    comp_svc_excs.DuplicateComponentLabelError,
):
    """
    An error that is raised when a agent profile with the same `label` as the agent profile being
    registered has already been registered with the agent profiles service.
    """

    code = "DUPLICATE_AGENT_PROFILE_LABEL_ERROR"

    def __init__(self, agent_profile_str: str, label: str):
        super().__init__(
            component_str=agent_profile_str,
            label=label,
        )


class AgentProfileDependencyError(
    AgentProfilesServiceError,
    comp_svc_excs.ComponentDependencyError,
):
    """
    Base exception for all errors that occur during the resolution of a plugin's
    dependencies.
    """

    code = "AGENT_PROFILE_DEPENDENCY_ERROR"

    _COMPONENT_TYPE = "agent profile"


class ThirdPartyDependencyNotFoundError(
    AgentProfileDependencyError,
    comp_svc_excs.ThirdPartyDependencyNotFoundError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is not
    installed.
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
    comp_svc_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """
    An error that is raised when a third-party dependency required by a plugin is
    incompatible with the plugin.
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
    comp_svc_excs.ComponentDependencyNotFoundError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is not
    installed.
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
    comp_svc_excs.IncompatibleComponentDependencyVersionError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is
    incompatible with the plugin.
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
    comp_svc_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """
    An error that is raised when a plugin depends on another plugin dependency that
    itself has invalid dependencies.
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
    comp_svc_excs.ComponentDependencyNotRunningError,
):
    """
    An error that is raised when a plugin dependency required by a plugin is present but
    not currently running.
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


# from typing import Literal
#
# from consortium.server.exceptions.service_exceptions.base_service_exception import (
#     BaseServiceException,
# )
#
#
# class AgentProfilesServiceError(BaseServiceException):
#     pass
#
#
# class AgentProfileNotFoundError(AgentProfilesServiceError):
#     def __init__(self, agent_profile_id: str):
#         super().__init__(
#             message=(
#                 f"Failed to find the requested agent profile. No agent profile was "
#                 f"found with the provided agent profile ID '{agent_profile_id}'."
#             ),
#         )
#
#
# class AgentProfileLoadError(AgentProfilesServiceError):
#     pass
#
#
# class InvalidAgentProjectManifestFileError(AgentProfileLoadError):
#     pass
#
#
# class AgentProjectManifestFileInvalidJSONError(
#     InvalidAgentProjectManifestFileError,
# ):
#     def __init__(self, agent_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project at '{agent_project_folder}'. The agent "
#                 f"project manifest file in the agent project folder is not a valid "
#                 f"JSON file."
#             ),
#         )
#
#
# class AgentProjectManifestFileSchemaError(
#     InvalidAgentProjectManifestFileError,
# ):
#     def __init__(self, agent_project_folder: str, json_schema_error_message: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the agent project at '{agent_project_folder}'. The "
#                 f"agent project manifest file in the agent project folder failed JSON "
#                 f"schema validation: {json_schema_error_message}"
#             ),
#         )
#
#
# class InvalidAgentProjectFolderStructureError(AgentProfileLoadError):
#     pass
#
#
# class AgentProjectManifestFileNotFoundError(
#     InvalidAgentProjectFolderStructureError,
# ):
#     def __init__(self, agent_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the agent project at '{agent_project_folder}'. The "
#                 f"agent project manifest file was not found in the agent project "
#                 f"folder."
#             ),
#         )
#
#
# class AgentProjectAgentGeneratorFileNotFoundError(
#     InvalidAgentProjectFolderStructureError,
# ):
#     def __init__(self, agent_generator_file: str, agent_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project folder at '{agent_project_folder}'. "
#                 f"Agent generator file '{agent_generator_file}' specified in the agent "
#                 f"project manifest file was not found."
#             ),
#         )
#
#
# class AgentProjectAgentTemplateFileNotFoundError(
#     InvalidAgentProjectFolderStructureError,
# ):
#     def __init__(self, agent_template_file: str, agent_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project folder at '{agent_project_folder}'. "
#                 f"Agent template file '{agent_template_file}' specified in the agent "
#                 f"project manifest file was not found."
#             ),
#         )
#
#
# class AgentProjectAgentTypeFileNotFoundError(
#     InvalidAgentProjectFolderStructureError,
# ):
#     def __init__(self, agent_type_file: str, agent_project_folder: str):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project folder at '{agent_project_folder}'. "
#                 f"Agent type file '{agent_type_file}' specified in the agent project "
#                 f"manifest file was not found."
#             ),
#         )
#
#
# class InvalidAgentProjectImplementationError(AgentProfileLoadError):
#     pass
#
#
# class AgentProjectInterfaceError(InvalidAgentProjectImplementationError):
#     def __init__(
#         self,
#         agent_project_file_type: Literal[
#             "agent generator",
#             "agent template",
#             "agent type",
#         ],
#         agent_project_folder: str,
#         agent_project_symbol: str,
#     ):
#         super().__init__(
#             message=(
#                 f"Failed to load the agent project at '{agent_project_folder}'. The "
#                 f"{agent_project_file_type} in the agent project folder does not "
#                 f"implement the required interface for its defined symbol "
#                 f"'{agent_project_symbol}'."
#             ),
#         )
#
#
# class AgentProjectSymbolNotFoundError(InvalidAgentProjectImplementationError):
#     def __init__(
#         self,
#         symbol_name: str,
#         agent_project_file: str,
#         agent_project_folder: str,
#         agent_project_file_type: Literal[
#             "agent generator",
#             "agent template",
#             "agent type",
#         ],
#     ):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project at '{agent_project_folder}'. The symbol "
#                 f"name '{symbol_name}' specified in the agent project's manifest file "
#                 f"was not found in the {agent_project_file_type} file "
#                 f"'{agent_project_file}'."
#             ),
#         )
#
#
# class InternalAgentProjectError(InvalidAgentProjectImplementationError):
#     def __init__(
#         self,
#         agent_project_file_type: Literal[
#             "agent generator",
#             "agent template",
#             "agent type",
#         ],
#         agent_project_folder: str,
#         error_message: str,
#     ):
#         super().__init__(
#             message=(
#                 f"Failed to load agent project at '{agent_project_folder}'. An "
#                 f"exception occurred while loading the {agent_project_file_type}: "
#                 f"{error_message}"
#             ),
#         )
