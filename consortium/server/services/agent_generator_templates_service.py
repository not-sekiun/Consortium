import importlib
import json
from pathlib import Path
from typing import Type

import jsonschema
from loguru import logger

from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.base_agent_generator_template import (
    BaseAgentGeneratorTemplate,
)
from consortium.server.framework.framework_types import AgentType
from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_HOME_DIRECTORY_PATH,
)
from consortium.server.server_exceptions import (
    InternalAgentProjectError,
    InvalidAgentProjectFolderStructureError,
    InvalidAgentProjectImplementationError,
    InvalidAgentProjectManifestFileError,
)


class AgentGeneratorTemplatesService:
    def __init__(self):
        self._agent_generator_templates = {}
        self._agent_generator_templates_service_logger = logger.bind(
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
                # Instantiate and load the agent generator template into the agent
                # generator templates service. This represents the loading of an agent.
                agent_generator_template = self._load_agent_from_agent_project_folder(
                    agent_project_folder_path.parent,
                )
                self._agent_generator_templates[
                    str(agent_generator_template.agent_generator_template_id)
                ] = agent_generator_template

                # Although we are explicitly loading the agent generator template here,
                # the loading of an agent generator template represents the framework
                # loading an entire agent.
                self._agent_generator_templates_service_logger.debug(
                    f"Loaded agent: {agent_generator_template!r}",
                )
                self._agent_generator_templates_service_logger.info(
                    f"Loaded agent: {agent_generator_template}",
                )
            except (
                InvalidAgentProjectFolderStructureError,
                InvalidAgentProjectManifestFileError,
                InvalidAgentProjectImplementationError,
                InternalAgentProjectError,
            ) as exc:
                self._agent_generator_templates_service_logger.error(
                    f"Failed to load agent. {exc}",
                )

    # Loading an agent is represented by the loading of an agent generator template into
    # the agent generator templates service hence the naming of this method.
    @staticmethod
    def _load_agent_from_agent_project_folder(
        agent_project_folder: Path,
    ) -> BaseAgentGeneratorTemplate:
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
                "agent_generator_template": {
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
                f"No agent project manifest file found in agent project folder: {agent_project_folder}",
            )
        except jsonschema.ValidationError:
            raise InvalidAgentProjectManifestFileError(
                f"Invalid agent_project_manifest.json file in agent project folder: {agent_project_folder}",
            )

        # Check for valid project folder structure as specified by the manifest file.
        agent_generator_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_generator"]["filepath"],
        )
        agent_generator_template_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_generator_template"]["filepath"],
        )
        agent_type_file = agent_project_folder / Path(
            agent_project_manifest_json["agent_type"]["filepath"],
        )

        if not agent_generator_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f"The agent generator file is missing for agent project folder: {agent_project_folder}",
            )
        if not agent_generator_template_file.exists():
            raise InvalidAgentProjectFolderStructureError(
                f"The agent generator template file is missing for agent project folder: {agent_project_folder}",
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
        agent_generator_template_module_path = ".".join(
            agent_generator_template_file.relative_to(
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
                f"Symbol name specified in agent_project_manifest.json was not found in the agent generator file for agent project folder: {agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent generator from {agent_project_folder} due to an exception during import: {exc}",
            )

        try:
            agent_generator_template_module = importlib.import_module(
                agent_generator_template_module_path,
            )
            agent_generator_template_class = getattr(
                agent_generator_template_module,
                agent_project_manifest_json["agent_generator_template"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f"Symbol name specified in agent_project_manifest.json was not found in the agent generator template file for agent project folder: {agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent generator template from {agent_project_folder} due to an exception during import: {exc}",
            )

        try:
            agent_type_module = importlib.import_module(agent_type_module_path)
            agent_type = getattr(
                agent_type_module,
                agent_project_manifest_json["agent_type"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidAgentProjectFolderStructureError(
                f"Symbol name specified in agent_project_manifest.json was not found in the agent type file for agent project folder: {agent_project_folder}",
            )
        except Exception as exc:
            raise InternalAgentProjectError(
                f"Failed to load agent type from {agent_project_folder} due to an exception during import: {exc}",
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(agent_generator_class, BaseAgentGenerator):
            raise InvalidAgentProjectImplementationError(
                f"The agent generator class must inherit from the framework's base agent generator class for agent project folder: {agent_project_folder}",
            )
        if not issubclass(agent_generator_template_class, BaseAgentGeneratorTemplate):
            raise InvalidAgentProjectImplementationError(
                f"The agent generator template class must inherit from the framework's base agent generator template class for agent project folder: {agent_project_folder}",
            )
        if not isinstance(agent_type, AgentType):
            raise InvalidAgentProjectImplementationError(
                f"The agent type must be an instance of the framework's agent type class for agent project folder: {agent_project_folder}",
            )

        # Return the instantiated agent generator template to be loaded into the
        # service.
        return agent_generator_template_class()

    def get_agent_generator_template_by_agent_generator_template_id(
        self,
        agent_generator_template_id: str,
    ) -> Type[BaseAgentGeneratorTemplate]:
        try:
            agent_generator_template = self._agent_generator_templates[
                agent_generator_template_id
            ]
        except KeyError:
            raise ValueError(
                f"No agent generator template exists with the provided agent generator template ID: {agent_generator_template_id}",
            )

        self._agent_generator_templates_service_logger.debug(
            f"Retrieved agent generator template: {agent_generator_template}",
        )
        return agent_generator_template

    def get_all_agent_generator_templates(
        self,
    ) -> list[Type[BaseAgentGeneratorTemplate]]:
        all_agent_generator_templates = list(self._agent_generator_templates.values())
        self._agent_generator_templates_service_logger.debug(
            f"Retrieved all agent generator templates ({len(all_agent_generator_templates)} retrieved)",
        )
        return all_agent_generator_templates
