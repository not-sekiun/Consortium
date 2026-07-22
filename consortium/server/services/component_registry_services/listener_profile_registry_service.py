import uuid

from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (
    ListenerProfileLoadingError,
)
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)


# The listener profile loader carries a listener profile exception set, so loading and
# registry errors are raised as listener profile types directly. This registry therefore
# extends the plain ComponentRegistryService rather than the exception remapping variant
# that the other domains still use.
class ListenerProfileRegistryService(
    ComponentRegistryService[
        ListenerProfile,
        ListenerProfileLoadingError,
    ],
):
    def _get_component_id(self, component: ListenerProfile) -> uuid.UUID:
        return component.listener_profile_id
