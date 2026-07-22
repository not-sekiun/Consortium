import uuid

from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileLoadingError,
)
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)


class AgentProfileRegistryService(
    ComponentRegistryService[AgentProfile, AgentProfileLoadingError],
):
    def _get_component_id(self, component: AgentProfile) -> uuid.UUID:
        return component.agent_profile_id
