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

from typing import Literal

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class AgentProfilesServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the agent profiles service.",
    ):
        super().__init__(message)


class AgentProfileNotFoundError(AgentProfilesServiceError):
    def __init__(self, agent_profile_id: str):
        super().__init__(
            "Failed to find the requested agent profile. No agent profile was "
            f"found with the provided agent profile ID '{agent_profile_id}'.",
        )


class AgentProfileLoadError(AgentProfilesServiceError):
    def __init__(
        self,
        message: str = "Failed to load agent profile. An error occurred while "
        "loading the agent profile.",
    ):
        super().__init__(message)


class InvalidAgentProjectManifestFileError(AgentProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load agent project. The agent project manifest file is "
            "invalid."
        ),
    ):
        super().__init__(message)


class AgentProjectManifestFileInvalidJSONError(
    InvalidAgentProjectManifestFileError,
):
    def __init__(self, agent_project_folder: str):
        super().__init__(
            "Failed to load agent project. The agent project manifest file "
            f"in agent project folder '{agent_project_folder}' is not a valid "
            f"JSON file.",
        )


class AgentProjectManifestFileSchemaError(
    InvalidAgentProjectManifestFileError,
):
    def __init__(self, agent_project_folder: str, json_schema_error_message: str):
        super().__init__(
            "Failed to load agent project. The agent project manifest file in "
            f"agent project folder '{agent_project_folder}' failed when "
            f"validating against the JSON schema: {json_schema_error_message}",
        )


class InvalidAgentProjectFolderStructureError(AgentProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load agent project folder. The agent project "
            "folder structure is invalid."
        ),
    ):
        super().__init__(message)


class AgentProjectManifestFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_project_folder: str):
        super().__init__(
            "Failed to load agent project. The agent project manifest file was "
            f"not found in the agent project folder '{agent_project_folder}'.",
        )


class AgentProjectAgentGeneratorFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_generator_file: str, agent_project_folder: str):
        super().__init__(
            f"Failed to load agent project folder. Agent generator file '{agent_generator_file}' "
            "specified in the agent project manifest file is missing for agent "
            f"project folder '{agent_project_folder}'.",
        )


class AgentProjectAgentTemplateFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_template_file: str, agent_project_folder: str):
        super().__init__(
            "Failed to load agent project folder. The agent template file "
            f"'{agent_template_file}' specified in the agent project manifest "
            f"file is missing for agent project folder '{agent_project_folder}'.",
        )


class AgentProjectAgentTypeFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_type_file: str, agent_project_folder: str):
        super().__init__(
            "Failed to load agent project folder. The agent type file "
            f"'{agent_type_file}' specified in the agent project manifest file "
            f"is missing for agent project folder '{agent_project_folder}'",
        )


class InvalidAgentProjectImplementationError(AgentProfileLoadError):
    def __init__(
        self,
        message: str = (
            "Failed to load agent profile. The agent project implementation is "
            "invalid."
        ),
    ):
        super().__init__(message)


class AgentProjectInterfaceError(InvalidAgentProjectImplementationError):
    def __init__(
        self,
        agent_project_file_type: Literal[
            "agent generator",
            "agent template",
            "agent type",
        ],
        agent_project_folder: str,
        agent_project_symbol: str,
    ):
        super().__init__(
            f"Failed to load agent profile. The {agent_project_file_type} in "
            f"agent project folder '{agent_project_folder}' does not implement "
            f"the required interface for its symbol '{agent_project_symbol}'.",
        )


class AgentProjectSymbolNotFoundError(InvalidAgentProjectImplementationError):
    def __init__(
        self,
        symbol_name: str,
        agent_project_file: str,
        agent_project_folder: str,
        agent_project_file_type: Literal[
            "agent generator",
            "agent template",
            "agent type",
        ],
    ):
        super().__init__(
            f"Failed to load agent project. The symbol name '{symbol_name}' "
            "specified in the agent project manifest file was not found in the "
            f"{agent_project_file_type} file '{agent_project_file}' for agent "
            f"project folder '{agent_project_folder}'",
        )


class InternalAgentProjectError(InvalidAgentProjectImplementationError):
    def __init__(
        self,
        agent_project_file_type: Literal[
            "agent generator",
            "agent template",
            "agent type",
        ],
        agent_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            "Failed to load agent profile. An exception occurred while loading the "
            f"{agent_project_file_type} from agent project folder "
            f"'{agent_project_folder}': {internal_error_message}",
        )
