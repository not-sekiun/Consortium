import importlib
import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileLoadError,
    AgentProfileNotFoundError,
    AgentProjectAgentGeneratorFileNotFoundError,
    AgentProjectAgentTemplateFileNotFoundError,
    AgentProjectAgentTypeFileNotFoundError,
    AgentProjectInterfaceError,
    AgentProjectManifestFileInvalidJSONError,
    AgentProjectManifestFileNotFoundError,
    AgentProjectManifestFileSchemaError,
    AgentProjectSymbolNotFoundError,
    InternalAgentProjectError,
)
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

    def __str__(self) -> str:
        return "Agent Profiles Service"

    def __repr__(self) -> str:
        return "AgentProfilesService()"

    def get_agent_profile_from_agent_project_folder(
        self,
        agent_project_folder: Path,
        ignore_enabled_agent_project_flag: bool = False,
    ) -> AgentProfile | None:
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
                    "required": ["filepath", "symbol"],
                    "additionalProperties": False,
                },
                "agent_template": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                    "required": ["filepath", "symbol"],
                    "additionalProperties": False,
                },
                "agent_type": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                    "required": ["filepath", "symbol"],
                    "additionalProperties": False,
                },
                "enabled": {"type": "boolean"},
            },
            "required": ["agent_generator", "agent_template", "agent_type", "enabled"],
            "additionalProperties": False,
        }
        try:
            with agent_project_manifest_file.open("r") as file:
                agent_project_manifest_json = json.load(fp=file)
                jsonschema.validate(
                    instance=agent_project_manifest_json,
                    schema=agent_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise AgentProjectManifestFileNotFoundError(
                agent_project_folder=str(agent_project_folder),
            )
        except json.JSONDecodeError:
            raise AgentProjectManifestFileInvalidJSONError(
                agent_project_folder=str(agent_project_folder),
            )
        except jsonschema.ValidationError as exc:
            raise AgentProjectManifestFileSchemaError(
                agent_project_folder=str(agent_project_folder),
                json_schema_error_message=exc.message,
            )

        if (
            not agent_project_manifest_json["enabled"]
            and not ignore_enabled_agent_project_flag
        ):
            self.agent_profiles_service_logger.info(
                "Skipped loading agent from '{}' because it was disabled.",
                str(agent_project_folder),
            )
            return None

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
            raise AgentProjectAgentGeneratorFileNotFoundError(
                agent_project_folder=str(agent_project_folder),
                agent_generator_file=str(agent_generator_file),
            )
        if not agent_template_file.exists():
            raise AgentProjectAgentTemplateFileNotFoundError(
                agent_project_folder=str(agent_project_folder),
                agent_template_file=str(agent_template_file),
            )
        if not agent_type_file.exists():
            raise AgentProjectAgentTypeFileNotFoundError(
                agent_project_folder=str(agent_project_folder),
                agent_type_file=str(agent_type_file),
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
            raise AgentProjectSymbolNotFoundError(
                symbol_name=str(agent_generator_symbol),
                agent_project_file=str(agent_generator_file),
                agent_project_file_type="agent generator",
                agent_project_folder=str(agent_project_folder),
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                agent_project_file_type="agent generator",
                agent_project_folder=str(agent_project_folder),
                error_message=str(exc),
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
            raise AgentProjectSymbolNotFoundError(
                symbol_name=str(agent_generator_symbol),
                agent_project_file=str(agent_generator_file),
                agent_project_file_type="agent template",
                agent_project_folder=str(agent_project_folder),
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                agent_project_file_type="agent template",
                agent_project_folder=str(agent_project_folder),
                error_message=str(exc),
            )

        try:
            agent_type_module = importlib.import_module(agent_type_module_path)
            agent_type = getattr(
                agent_type_module,
                agent_type_symbol,
            )
        except (ImportError, AttributeError):
            raise AgentProjectSymbolNotFoundError(
                symbol_name=str(agent_generator_symbol),
                agent_project_file=str(agent_generator_file),
                agent_project_file_type="agent type",
                agent_project_folder=str(agent_project_folder),
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                agent_project_file_type="agent type",
                agent_project_folder=str(agent_project_folder),
                error_message=str(exc),
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(agent_generator_class, BaseAgentGenerator):
            raise AgentProjectInterfaceError(
                agent_project_file_type="agent generator",
                agent_project_folder=str(agent_project_folder),
                agent_project_symbol=str(agent_generator_symbol),
            )
        if not issubclass(agent_template_class, BaseAgentTemplate):
            raise AgentProjectInterfaceError(
                agent_project_file_type="agent template",
                agent_project_folder=str(agent_project_folder),
                agent_project_symbol=str(agent_generator_symbol),
            )
        if not isinstance(agent_type, BaseAgentType):
            raise AgentProjectInterfaceError(
                agent_project_file_type="agent type",
                agent_project_folder=str(agent_project_folder),
                agent_project_symbol=str(agent_generator_symbol),
            )

        try:
            agent_template_object = agent_template_class()
        except Exception as exc:
            raise InternalAgentProjectError(
                agent_project_file_type="agent template",
                agent_project_folder=str(agent_project_folder),
                error_message=str(exc),
            )

        return AgentProfile(
            name=agent_template_object.name,
            agent_generator=agent_generator_class,
            agent_template=agent_template_object,
            agent_type=agent_type,
            agent_project_folder_path=agent_project_folder,
        )

    def load_framework_agent_profiles(self) -> list[AgentProfile]:
        self.agent_profiles_service_logger.info(
            "Loading framework agent profiles...",
        )

        for path in CONSORTIUM_AGENTS_DIRECTORY_PATH.rglob("*"):
            if path.name != "agent_project_manifest.json":
                continue

            try:
                agent_profile = self.load_agent_profile_from_agent_project_folder(
                    agent_project_folder=path.parent,
                )

                if agent_profile is None:
                    continue

                self.agent_profiles_service_logger.success(
                    "Loaded agent profile: {}",
                    agent_profile,
                )
            except AgentProfileLoadError as exc:
                self.agent_profiles_service_logger.error(exc)

        all_agent_profiles = self.get_all_agent_profiles()
        self.agent_profiles_service_logger.info(
            f"Loaded framework agent profiles ({len(all_agent_profiles)} "
            "agent profile(s) loaded).",
        )
        return all_agent_profiles

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
        self.agent_profiles_service_logger.info("Reloaded framework agent profiles.")
        return agent_profiles

    def load_agent_profile_from_agent_project_folder(
        self,
        agent_project_folder: Path,
    ) -> AgentProfile | None:
        agent_profile = self.get_agent_profile_from_agent_project_folder(
            agent_project_folder,
        )

        # `agent_profile` being `None` implies a disabled listener profile was
        # attempted to be loaded.
        if agent_profile is None:
            return None

        self._agent_profiles[str(agent_profile.agent_profile_id)] = agent_profile
        self.agent_profiles_service_logger.debug(
            f"Loaded agent profile: {agent_profile!r}",
        )
        return agent_profile

    def unload_agent_profile_by_agent_profile_id(self, agent_profile_id) -> None:
        try:
            agent_profile = self._agent_profiles.pop(agent_profile_id)
        except KeyError:
            raise AgentProfileNotFoundError(agent_profile_id=agent_profile_id)

        self.agent_profiles_service_logger.info(
            f"Unloaded agent profile: {agent_profile}",
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
            raise AgentProfileNotFoundError(agent_profile_id=agent_profile_id)

        agent_profile = self.load_agent_profile_from_agent_project_folder(
            agent_profile.agent_project_folder_path,
        )
        self.agent_profiles_service_logger.info(
            f"Reloaded agent profile: {agent_profile}",
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
            raise AgentProfileNotFoundError(agent_profile_id=agent_profile_id)

        self.agent_profiles_service_logger.debug(
            f"Retrieved agent profile: {agent_profile!r}",
        )
        return agent_profile
