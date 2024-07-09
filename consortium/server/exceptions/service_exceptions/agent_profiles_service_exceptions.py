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
    pass


class AgentProfileNotFoundError(AgentProfilesServiceError):
    def __init__(self, agent_profile_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested agent profile. No agent profile was "
                f"found with the provided agent profile ID '{agent_profile_id}'."
            ),
        )


class AgentProfileLoadError(AgentProfilesServiceError):
    pass


class InvalidAgentProjectManifestFileError(AgentProfileLoadError):
    pass


class AgentProjectManifestFileInvalidJSONError(
    InvalidAgentProjectManifestFileError,
):
    def __init__(self, agent_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load agent project at '{agent_project_folder}'. The agent "
                f"project manifest file in the agent project folder is not a valid "
                f"JSON file."
            ),
        )


class AgentProjectManifestFileSchemaError(
    InvalidAgentProjectManifestFileError,
):
    def __init__(self, agent_project_folder: str, json_schema_error_message: str):
        super().__init__(
            message=(
                f"Failed to load the agent project at '{agent_project_folder}'. The "
                f"agent project manifest file in the agent project folder failed JSON "
                f"schema validation: {json_schema_error_message}"
            ),
        )


class InvalidAgentProjectFolderStructureError(AgentProfileLoadError):
    pass


class AgentProjectManifestFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load the agent project at '{agent_project_folder}'. The "
                f"agent project manifest file was not found in the agent project "
                f"folder."
            ),
        )


class AgentProjectAgentGeneratorFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_generator_file: str, agent_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load agent project folder at '{agent_project_folder}'. "
                f"Agent generator file '{agent_generator_file}' specified in the agent "
                f"project manifest file was not found."
            ),
        )


class AgentProjectAgentTemplateFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_template_file: str, agent_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load agent project folder at '{agent_project_folder}'. "
                f"Agent template file '{agent_template_file}' specified in the agent "
                f"project manifest file was not found."
            ),
        )


class AgentProjectAgentTypeFileNotFoundError(
    InvalidAgentProjectFolderStructureError,
):
    def __init__(self, agent_type_file: str, agent_project_folder: str):
        super().__init__(
            message=(
                f"Failed to load agent project folder at '{agent_project_folder}'. "
                f"Agent type file '{agent_type_file}' specified in the agent project "
                f"manifest file was not found."
            ),
        )


class InvalidAgentProjectImplementationError(AgentProfileLoadError):
    pass


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
            message=(
                f"Failed to load the agent project at '{agent_project_folder}'. The "
                f"{agent_project_file_type} in the agent project folder does not "
                f"implement the required interface for its defined symbol "
                f"'{agent_project_symbol}'."
            ),
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
            message=(
                f"Failed to load agent project at '{agent_project_folder}'. The symbol "
                f"name '{symbol_name}' specified in the agent project's manifest file "
                f"was not found in the {agent_project_file_type} file "
                f"'{agent_project_file}'."
            ),
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
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to load agent project at '{agent_project_folder}'. An "
                f"exception occurred while loading the {agent_project_file_type}: "
                f"{error_message}"
            ),
        )
