import importlib
import pathlib
from typing import Type

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


class AgentGeneratorTemplatesService:
    def __init__(self):
        self._agent_generator_templates = {}
        self._agent_generator_templates_service_logger = logger.bind(
            logger_name="Consortium Agent Generator Templates Service",
        )

        # attempt to recursively load each folder as a agent generator project folder
        visited_dir_paths = []
        for agent_project_folder_path in CONSORTIUM_AGENTS_DIRECTORY_PATH.rglob("*"):
            if agent_project_folder_path.parent in visited_dir_paths:
                continue
            visited_dir_paths.append(agent_project_folder_path.parent)
            try:
                self._load_agent_project_folder(agent_project_folder_path.parent)
            # triggers for invalid project folder structure
            except ValueError:
                pass

    def _load_agent_project_folder(self, agent_project_folder_path: pathlib.Path):
        # An agent project folder is a folder that represents a valid agent that can be
        # loaded into the server. It is defined as a folder that contains an
        # agent_generator.py file, an agent_generator_template.py file, and an
        # agent_type.py file. The agent_generator.py file must contain a class called
        # AgentGenerator that inherits from BaseAgentGenerator. The
        # agent_generator_template.py file must contain a class called
        # AgentGeneratorTemplate that inherits from BaseAgentGeneratorTemplate. The
        # agent_type.py file must contain the constant AGENT_TYPE which is an instance
        # of AgentType. The folder must be located at consortium/server/framework/agents
        # with any arbitrary nested folder structure. On top of that, the folder must be
        # a valid python package reachable from the root of the server. This means that
        # the folder must contain __init__.py files in all parent directories.
        files_in_directory = [
            file.name for file in agent_project_folder_path.iterdir() if file.is_file()
        ]

        # check for valid project folder structure
        if (
            "agent_generator.py" not in files_in_directory
            or "agent_generator_template.py" not in files_in_directory
            or "agent_type.py" not in files_in_directory
            or "__init__.py" not in files_in_directory
        ):
            raise ValueError(
                f"The folder {agent_project_folder_path} is not a valid agent project folder. It must contain the following files: agent_generator.py, agent_generator_template.py, agent_type.py, __init__.py",
            )

        relative_path = agent_project_folder_path.relative_to(
            CONSORTIUM_HOME_DIRECTORY_PATH,
        )
        module_name = ".".join(relative_path.parts)

        # Check to see if any errors arise during import.
        try:
            agent_generator_module = importlib.import_module(
                f"{module_name}.agent_generator",
            )
            agent_generator_template_module = importlib.import_module(
                f"{module_name}.agent_generator_template",
            )
            agent_type_module = importlib.import_module(
                f"{module_name}.agent_type",
            )
        except Exception as exc:
            self._agent_generator_templates_service_logger.error(
                f"Failed to load agent from {agent_project_folder_path} due to exception: {exc}",
            )
            return

        # check for valid naming of classes
        try:
            agent_generator = agent_generator_module.AgentGenerator
            agent_generator_template = (
                agent_generator_template_module.AgentGeneratorTemplate
            )
            agent_type = agent_type_module.AGENT_TYPE
        except AttributeError:
            self._agent_generator_templates_service_logger.error(
                f"Failed to load agent from {agent_project_folder_path} due to missing classes",
            )
            return

        # check if the agent generator and agent generator template classes are valid
        if not issubclass(agent_generator, BaseAgentGenerator):
            raise ValueError(
                f"The agent generator class in the folder {agent_project_folder_path} must inherit from BaseAgentGenerator",
            )
        if not issubclass(agent_generator_template, BaseAgentGeneratorTemplate):
            raise ValueError(
                f"The agent generator template class in the folder {agent_project_folder_path} must inherit from BaseAgentGeneratorTemplate",
            )
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"The agent type class in the folder {agent_project_folder_path} must inherit from AgentType",
            )

        instantiated_agent_generator_template = agent_generator_template()
        self._agent_generator_templates[
            str(instantiated_agent_generator_template.agent_template_id)
        ] = instantiated_agent_generator_template

        # Although we are explicitly loading the agent generator template here, the
        # loading of an agent generator template represents the framework loading an
        # entire agent.
        self._agent_generator_templates_service_logger.debug(
            f"Loaded agent: {instantiated_agent_generator_template.name} ({instantiated_agent_generator_template.agent_template_id})",
        )

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
                f"Agent generator template with the agent generator template ID {agent_generator_template_id} does not exist",
            )

        self._agent_generator_templates_service_logger.debug(
            f'Retrieved agent generator template: "{agent_generator_template.name}" {agent_generator_template_id}',
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
