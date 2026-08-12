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
        # Declared types are registered before `on_setup` runs, not after. The events
        # service is the single source of truth for a hook's subscriptions and
        # `subscribe_to_event_type`/`unsubscribe_from_event_type` reach it unconditionally,
        # so a hook that resolves further subscriptions at runtime (from a configuration
        # file, for example) needs the declared set already registered by the time
        # `on_setup` runs: otherwise a subscribe call from `on_setup` would race the bulk
        # registration below (double-registering the same type), and an unsubscribe call
        # for a declared type would find nothing registered yet and silently no-op.
        # Registering first means a failed `on_setup` can leave the declared handlers
        # behind, so both except blocks below roll the registration back explicitly.
        for event_type in type(component).event_types:
            self._events_service.register_event_handler_to_event_type(
                event_type=event_type,
                event_handler=component.on_triggered,
            )

        try:
            await component.on_setup()
        except event_hook_framework_excs.EventHookSetupError as exc:
            self._deregister_all_event_types(component)
            raise EventHookSetupError(
                event_hook_str=str(component),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self._deregister_all_event_types(component)
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
        self._deregister_all_event_types(component)
        return component

    # Deregistration is driven by what is actually registered with the events service,
    # rather than by the hook's declared or (formerly) locally-tracked subscriptions,
    # which may have changed after (or during) loading. Using the declared set would try
    # to remove subscriptions that were never registered and leave behind ones added at
    # runtime. Shared by both `_component_load_procedure` except blocks (rolling back a
    # failed setup) and `_component_unload_procedure`.
    def _deregister_all_event_types(self, component: BaseEventHook) -> None:
        registered_event_types = (
            self._events_service.get_event_types_from_registered_event_handler(
                event_handler=component.on_triggered,
            )
        )
        for event_type in registered_event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=component.on_triggered,
            )
