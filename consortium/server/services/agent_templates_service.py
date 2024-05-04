import importlib
import json
from pathlib import Path
from typing import Type

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
from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_HOME_DIRECTORY_PATH,
)


class AgentTemplatesService:
    def __init__(self):
        self._agent_templates = {}
        self._agent_templates_service_logger = logger.bind(
            logger_name="Consortium Agent Generator Templates Service",
        )

        # Recursively search through the agents directory to load all agent
        # projects.
        for agent_project_folder_path in CONSORTIUM_AGENTS_DIRECTORY_PATH.rglob(
            "*",
        ):
            if agent_project_folder_path.name != "agent_project_manifest.json":
                continue

            try:
                # Instantiate and load the agent template into the agent
                # generator templates service. This represents the loading of an agent.
                agent_template = self._load_agent_from_agent_project_folder(
                    agent_project_folder_path.parent,
                )
                self._agent_templates[str(agent_template.agent_template_id)] = (
                    agent_template
                )

                # Although we are explicitly loading the agent template here,
                # the loading of an agent template represents the framework
                # loading an entire agent.
                self._agent_templates_service_logger.debug(
                    f"Loaded agent: {agent_template!r}",
                )
                self._agent_templates_service_logger.info(
                    f"Loaded agent: {agent_template}",
                )
            except (
                InvalidAgentProjectFolderStructureError,
                InvalidAgentProjectManifestFileError,
                InvalidAgentProjectImplementationError,
                InternalAgentProjectError,
            ) as exc:
                self._agent_templates_service_logger.error(
                    f"Failed to load agent. {exc}",
                )

    # Loading an agent is represented by the loading of an agent template into
    # the agent templates service hence the naming of this method.
    @staticmethod
    def _load_agent_from_agent_project_folder(
        agent_project_folder: Path,
    ) -> BaseAgentTemplate:
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
                f"No agent project manifest file found in agent project folder: "
                f"{agent_project_folder}",
            )
        except jsonschema.ValidationError:
            raise InvalidAgentProjectManifestFileError(
                f"Invalid agent_project_manifest.json file in agent project folder: "
                f"{agent_project_folder}",
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
                f"The agent generator file is missing for agent project folder: {agent_project_folder}",
            )
        if not agent_template_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f"The agent template file is missing for agent project folder: {agent_project_folder}",
            )
        if not agent_type_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f"The agent type file is missing for agent project folder: {agent_project_folder}",
            )

        # Check for valid symbol names in the required agent project files.
        agent_generator_module_path = ".".join(
            agent_generator_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        agent_template_module_path = ".".join(
            agent_template_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        agent_type_module_path = ".".join(
            agent_type_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]

        try:
            agent_generator_module = importlib.import_module(
                agent_generator_module_path,
            )
            agent_generator_class = getattr(
                agent_generator_module,
                agent_project_manifest_json["agent_generator"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f"Symbol name specified in agent_project_manifest.json was not found "
                f"in the agent generator file for agent project folder: "
                f"{agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent generator from {agent_project_folder} due to an "
                f"exception during import: {exc}",
            )

        try:
            agent_template_module = importlib.import_module(
                agent_template_module_path,
            )
            agent_template_class = getattr(
                agent_template_module,
                agent_project_manifest_json["agent_template"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f"Symbol name specified in agent_project_manifest.json was not found "
                f"in the agent template file for agent project folder: "
                f"{agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent template from {agent_project_folder} due to an "
                f"exception during import: {exc}",
            )

        try:
            agent_type_module = importlib.import_module(agent_type_module_path)
            agent_type = getattr(
                agent_type_module,
                agent_project_manifest_json["agent_type"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f"Symbol name specified in agent_project_manifest.json was not found "
                f"in the agent type file for agent project folder: "
                f"{agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent type from {agent_project_folder} due to an "
                f"exception during import: {exc}",
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(agent_generator_class, BaseAgentGenerator):
            raise InvalidAgentProjectImplementationError(
                f"The agent generator class must inherit from the framework's base "
                f"agent generator class for agent project folder: "
                f"{agent_project_folder}",
            )
        if not issubclass(agent_template_class, BaseAgentTemplate):
            raise InvalidAgentProjectImplementationError(
                f"The agent template class must inherit from the framework's base "
                f"agent template class for agent project folder: "
                f"{agent_project_folder}",
            )
        if not isinstance(agent_type, AgentType):
            raise InvalidAgentProjectImplementationError(
                f"The agent type must be an instance of the framework's agent type "
                f"class for agent project folder: {agent_project_folder}",
            )

        # Return the instantiated agent template to be loaded into the
        # service.
        return agent_template_class()

    def get_agent_template_by_agent_template_id(
        self,
        agent_template_id: str,
    ) -> Type[BaseAgentTemplate]:
        try:
            agent_template = self._agent_templates[agent_template_id]
        except KeyError:
            raise ValueError(
                f"No agent template exists with the provided agent template ID: "
                f"{agent_template_id}",
            )

        self._agent_templates_service_logger.debug(
            f"Retrieved agent template: {agent_template}",
        )
        return agent_template

    def get_all_agent_templates(
        self,
    ) -> list[Type[BaseAgentTemplate]]:
        all_agent_templates = list(self._agent_templates.values())
        self._agent_templates_service_logger.debug(
            f"Retrieved all agent templates ({len(all_agent_templates)} retrieved)",
        )
        return all_agent_templates
