import pathlib
import uuid

from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.framework.signal_exceptions import (
    event_hooks_signal_exceptions as event_hook_framework_excs,
)
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    EventHookLoadingError,
    EventHookSetupError,
    EventHookTeardownError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
)
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)
from consortium.server.services.events_service import EventsService


# The event hook loader carries an event hook exception set, so loading and registry errors
# are raised as event hook types directly. This registry therefore extends the plain
# ComponentRegistryService rather than the exception remapping variant that the other
# domains still use.
class EventHookRegistryService(
    ComponentRegistryService[BaseEventHook, EventHookLoadingError],
):
    def __init__(
        self,
        component_loader_service: ComponentLoaderService,
        component_framework_directory: pathlib.Path,
        events_service: EventsService,
    ) -> None:
        super().__init__(
            component_loader_service=component_loader_service,
            component_framework_directory=component_framework_directory,
        )
        self._events_service = events_service

    def _get_component_id(self, component: BaseEventHook) -> uuid.UUID:
        return component.event_hook_id

    async def _component_load_procedure(
        self,
        component: BaseEventHook,
        context: dict,
    ) -> BaseEventHook:
        for event_type in component.event_types:
            self._events_service.register_event_handler_to_event_type(
                event_type=event_type,
                event_handler=component.on_triggered,
            )
        try:
            await component.on_setup()
        except event_hook_framework_excs.EventHookSetupError as exc:
            raise EventHookSetupError(
                event_hook_str=str(component),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            raise EventHookSetupError(
                event_hook_str=str(component),
                error_message=(
                    f"An unhandled exception was raised while setting up. "
                    f"{type(exc).__name__}: {exc}"
                ),
                detail={"type": type(exc).__name__, "message": str(exc)},
            ) from exc
        return component

    async def _component_unload_procedure(
        self,
        component: BaseEventHook,
        context: dict,
    ) -> BaseEventHook:
        try:
            await component.on_teardown()
        except event_hook_framework_excs.EventHookTeardownError as exc:
            raise EventHookTeardownError(
                event_hook_str=str(component),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            raise EventHookTeardownError(
                event_hook_str=str(component),
                error_message=(
                    f"An unhandled exception was raised while tearing down. "
                    f"{type(exc).__name__}: {exc}"
                ),
                detail={"type": type(exc).__name__, "message": str(exc)},
            ) from None
        for event_type in component.event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=component.on_triggered,
            )
        return component
