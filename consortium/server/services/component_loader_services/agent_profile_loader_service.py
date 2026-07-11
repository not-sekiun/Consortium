import pathlib

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilitiesFrameworkError,
)
from consortium.framework._core.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorsFrameworkError,
)
from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplatesFrameworkError,
)
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentLoadingError,
)
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.services.component_loader_services.component_loader_service import (
    Component,
    ComponentLoaderService,
)


class AgentProfileLoaderService(ComponentLoaderService[BaseAgentTemplate]):
    _component_type = BaseAgentTemplate  # TODO: Fix type mismatch this only describes the input but not output type
    _component_framework_error = (
        AgentTemplatesFrameworkError,
        AgentGeneratorsFrameworkError,
        AgentCapabilitiesFrameworkError,
    )
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }

    @staticmethod
    def _post_validate_component_object(
        component_object: BaseAgentTemplate,
    ) -> AgentProfile:
        # agent generator refers to the class of the agent generator that the
        # template creates
        component_object.agent_generator.creating_agent_template = component_object
        # Framework user passes in the agent type class, instantiate the agent type
        component_object.agent_type = component_object.agent_type()
        component_object.agent_generator.agent_type = component_object.agent_type
        component_object.agent_generator.compatible_listener_types = (
            component_object.compatible_listener_types
        )
        return AgentProfile(
            agent_generator=component_object.agent_generator,
            agent_template=component_object,
            agent_type=component_object.agent_type,
        )

    # Change the return type to AgentProfile for IDE type checking
    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> AgentProfile | None:
        return super().get_component_from_component_project_folder(
            component_project_folder=component_project_folder,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    # Change the return type to AgentProfile for IDE type checking
    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[Component],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]],
    ]:
        return super().get_components_from_component_project_folder_directories(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )
