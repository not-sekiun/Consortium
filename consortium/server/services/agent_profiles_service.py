import importlib
import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.server.exceptions.internal_server_exceptions import (
    InternalAgentProjectError,
    InvalidAgentProjectFolderStructureError,
    InvalidAgentProjectImplementationError,
    InvalidAgentProjectManifestFileError,
)
from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.base_agent_template import BaseAgentTemplate
from consortium.server.framework.c2_types import AgentType
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_HOME_DIRECTORY_PATH,
)


# The agent profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API should not have access to this service.
class AgentProfilesService:
    def __init__(self):
        self._agent_profiles = {}
        self.agent_profiles_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.agent_profiles_service_logger.debug(
            f"Started {self}",
        )

    @staticmethod
    def get_agent_profile_from_agent_project_folder(
        agent_project_folder: Path,
    ) -> AgentProfile:
        # Check if project folder contains a valid manifest file.
        agent_project_manifest_file = (
            agent_project_folder / "agent_project_manifest.json"
        )
        agent_project_manifest_json_schema = {
            "type": "object",
            "properties": {
                "agent_generator": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
                "agent_template": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
                "agent_type": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
            },
        }
        try:
            with agent_project_manifest_file.open("r") as file:
                agent_project_manifest_json = json.load(fp=file)
                jsonschema.validate(
                    instance=agent_project_manifest_json,
                    schema=agent_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise InvalidAgentProjectFolderStructureError(
                "The agent project manifest file (agent_project_manifest.json) "
                "was not found in the agent project folder: "
                f"{agent_project_folder}",
            )
        except json.JSONDecodeError:
            raise InvalidAgentProjectManifestFileError(
                "The agent project manifest file (agent_project_manifest.json) "
                f'in the agent project folder "{agent_project_folder}" is not a '
                f"valid JSON file.",
            )
        except jsonschema.ValidationError as exc:
            raise InvalidAgentProjectManifestFileError(
                "The agent project manifest file (agent_project_manifest.json) "
                f'in the agent project folder "{agent_project_folder}" does not '
                f"follow the correct JSON schema: {exc}",
            )

        # Check for valid project folder structure as specified by the manifest file.
        agent_generator_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_generator"]["filepath"],
        )
        agent_template_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_template"]["filepath"],
        )
        agent_type_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_type"]["filepath"],
        )

        if not agent_generator_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f'The agent generator file "{agent_generator_file}" specified in the '
                "agent project manifest file (agent_project_manifest.json) is missing "
                f"for agent project folder: {agent_project_folder}",
            )
        if not agent_template_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f'The agent template file "{agent_template_file}" specified in '
                "the agent project manifest file (agent_project_manifest.json) "
                f"is missing for agent project folder: {agent_project_folder}",
            )
        if not agent_type_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f'The agent type file "{agent_type_file}" specified in the '
                "agent project manifest file (agent_project_manifest.json) is "
                f"missing for agent project folder: {agent_project_folder}",
            )

        # Check for valid symbol names in the required agent project files.
        agent_generator_module_path = ".".join(
            agent_generator_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        agent_generator_symbol = agent_project_manifest_json["agent_generator"][
            "symbol"
        ]
        agent_template_module_path = ".".join(
            agent_template_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        agent_template_symbol = agent_project_manifest_json["agent_template"]["symbol"]
        agent_type_module_path = ".".join(
            agent_type_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        agent_type_symbol = agent_project_manifest_json["agent_type"]["symbol"]

        try:
            agent_generator_module = importlib.import_module(
                agent_generator_module_path,
            )
            agent_generator_class = getattr(
                agent_generator_module,
                agent_generator_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f'The symbol name "{agent_generator_symbol}" specified in the agent '
                "project manifest file (agent_project_manifest.json) was not found "
                f'in the agent generator file "{agent_generator_file}" for agent '
                f"project folder: {agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent generator from {agent_project_folder} due to an "
                f"exception that occurred while importing the agent generator: {exc}",
            )

        try:
            agent_template_module = importlib.import_module(
                agent_template_module_path,
            )
            agent_template_class = getattr(
                agent_template_module,
                agent_template_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f'The symbol name "{agent_template_symbol}" specified in the '
                "agent project manifest file (agent_project_manifest.json) was "
                f'not found in the agent template file "{agent_template_file}" for '
                f"agent project folder: {agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent template from {agent_project_folder} due "
                f"to an exception that occurred while importing the agent template: "
                f"{exc}",
            )

        try:
            agent_type_module = importlib.import_module(agent_type_module_path)
            agent_type = getattr(
                agent_type_module,
                agent_type_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f'The symbol name "{agent_type_symbol}" specified in the agent '
                "project manifest file (agent_project_manifest.json) was not found "
                f'in the agent type file "{agent_type_file}" for agent project folder: '
                f"{agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent type from {agent_project_folder} due to "
                f"an exception that occurred while importing the agent type: {exc}",
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(agent_generator_class, BaseAgentGenerator):
            raise InvalidAgentProjectImplementationError(
                "The symbol name of the agent generator class specified in the agent "
                "project manifest file (agent_project_manifest.json) does not inherit "
                "from the framework's base agent generator class for the agent project "
                f"folder: {agent_project_folder}",
            )
        if not issubclass(agent_template_class, BaseAgentTemplate):
            raise InvalidAgentProjectImplementationError(
                "The symbol name of the agent template class specified in the "
                "agent project manifest file (agent_project_manifest.json) does "
                "not inherit from the framework's base agent template class for the "
                f"agent project folder: {agent_project_folder}",
            )
        if not isinstance(agent_type, AgentType):
            raise InvalidAgentProjectImplementationError(
                "The symbol name of the agent type specified in the agent "
                "project manifest file (agent_project_manifest.json) does not inherit "
                "from the framework's base agent type for the agent project "
                f"folder: {agent_project_folder}",
            )

        try:
            agent_template_object = agent_template_class()
        except Exception as exc:
            raise InternalAgentProjectError(
                "Failed to load agent template for agent project folder "
                f"{agent_project_folder} due to an exception that occurred while "
                f"instantiating the agent template: {exc}",
            )

        return AgentProfile(
            agent_generator=agent_generator_class,
            agent_template=agent_template_object,
            agent_type=agent_type,
            agent_project_folder_path=agent_project_folder,
        )

    def load_framework_agent_profiles(self) -> list[AgentProfile]:
        self.agent_profiles_service_logger.info(
            "Loading framework agent profiles...",
        )

        agent_profiles = []
        for path in CONSORTIUM_AGENTS_DIRECTORY_PATH.rglob("*"):
            if path.name != "agent_project_manifest.json":
                continue

            try:
                agent_profile = self.get_agent_profile_from_agent_project_folder(
                    path.parent,
                )
                agent_profiles.append(agent_profile)
                self._agent_profiles[str(agent_profile.agent_profile_id)] = (
                    agent_profile
                )
                self.agent_profiles_service_logger.info(
                    f"Loaded agent profile: {agent_profile}",
                )
                self.agent_profiles_service_logger.debug(
                    f"Loaded agent profile: {agent_profile!r}",
                )
            except (
                InvalidAgentProjectFolderStructureError,
                InvalidAgentProjectImplementationError,
                InvalidAgentProjectManifestFileError,
                InternalAgentProjectError,
            ) as exc:
                self.agent_profiles_service_logger.error(
                    f"Failed to load agent profile from agent project folder "
                    f"{path.parent}. {exc}",
                )

        self.agent_profiles_service_logger.info(
            f"Loaded framework agent profiles ({len(self._agent_profiles)} "
            "agent profile(s) loaded).",
        )
        return agent_profiles

    def unload_framework_agent_profiles(self) -> None:
        self.agent_profiles_service_logger.info(
            "Unloading framework agent profiles...",
        )
        number_of_agent_profiles = len(self._agent_profiles)
        self._agent_profiles = {}
        self.agent_profiles_service_logger.info(
            f"Unloaded framework agent profiles ({number_of_agent_profiles} "
            "agent profile(s) unloaded).",
        )

    def reload_framework_agent_profiles(self) -> list[AgentProfile]:
        self.agent_profiles_service_logger.info(
            "Reloading framework agent profiles...",
        )
        self.unload_framework_agent_profiles()
        agent_profiles = self.load_framework_agent_profiles()
        self.agent_profiles_service_logger.info(f"Reloaded framework agent profiles.")
        return agent_profiles

    def load_agent_profile_from_agent_project_folder(
        self,
        agent_project_folder: Path,
    ) -> AgentProfile:
        agent_profile = self.get_agent_profile_from_agent_project_folder(
            agent_project_folder,
        )
        self._agent_profiles[str(agent_profile.agent_profile_id)] = agent_profile
        self.agent_profiles_service_logger.debug(
            f"Loaded agent profile: {agent_profile!r}",
        )
        return agent_profile

    def unload_agent_profile_by_agent_profile_id(self, agent_profile_id) -> None:
        try:
            agent_profile = self._agent_profiles.pop(agent_profile_id)
        except KeyError:
            raise ValueError(
                f"No agent profile exists with the provided agent profile ID: "
                f"{agent_profile_id}",
            )

        self.agent_profiles_service_logger.debug(
            f"Unloaded agent profile: {agent_profile!r}",
        )
        return agent_profile

    def reload_agent_profile_by_agent_profile_id(
        self,
        agent_profile_id,
    ) -> AgentProfile:
        try:
            agent_profile = self._agent_profiles.pop(agent_profile_id)
        except KeyError:
            raise ValueError(
                f"No agent profile exists with the provided agent profile ID: "
                f"{agent_profile_id}",
            )

        agent_profile = self.load_agent_profile_from_agent_project_folder(
            agent_profile.agent_project_folder_path,
        )
        self.agent_profiles_service_logger.debug(
            f"Reloaded agent profile: {agent_profile!r}",
        )
        return agent_profile

    def get_all_agent_profiles(self):
        all_agent_profiles = list(self._agent_profiles.values())
        self.agent_profiles_service_logger.debug(
            f"Retrieved all agent profiles ({len(all_agent_profiles)} retrieved).",
        )
        return all_agent_profiles

    def get_agent_profile_by_agent_profile_id(self, agent_profile_id):
        try:
            agent_profile = self._agent_profiles[agent_profile_id]
        except KeyError:
            raise ValueError(
                f"No agent profile exists with the provided agent profile ID: "
                f"{agent_profile_id}",
            )

        self.agent_profiles_service_logger.debug(
            f"Retrieved agent profile: {agent_profile!r}",
        )
        return agent_profile

    def __str__(self) -> str:
        return "Consortium Agent Profiles Service"

    def __repr__(self) -> str:
        return "AgentProfilesService()"
