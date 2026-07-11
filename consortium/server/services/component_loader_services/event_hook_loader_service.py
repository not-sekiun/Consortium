from consortium.framework._core.framework_exceptions.event_hooks_framework_exceptions import (
    EventHooksFrameworkError,
)
from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
)


class EventHookLoaderService(ComponentLoaderService[BaseEventHook]):
    _component_type = BaseEventHook
    _component_framework_error = EventHooksFrameworkError
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }
