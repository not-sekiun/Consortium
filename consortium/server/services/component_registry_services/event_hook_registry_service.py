import pathlib
import uuid

from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.framework.signal_exceptions import (
    event_hooks_signal_exceptions as event_hook_framework_excs,
)
from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.event_hooks_consortium_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicateEventHookLabelError,
    EventHookAlreadyRegisteredError,
    EventHookDependsOnInvalidComponentDependencyError,
    EventHookLoadingError,
    EventHookNotFoundError,
    EventHookProjectEntryPointModuleNotFoundError,
    EventHookProjectInterfaceError,
    EventHookProjectManifestFileNotFoundError,
    EventHookProjectSymbolNotFoundError,
    EventHookSetupError,
    EventHookTeardownError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleEventHookFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalEventHookProjectError,
    InvalidEventHookProjectManifestFileJSONError,
    InvalidEventHookProjectManifestFileSchemaError,
    InvalidEventHookProjectPyProjectFileDependencyError,
    InvalidEventHookProjectPyProjectFileError,
    InvalidEventHookProjectPyProjectFileTOMLError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
)
from consortium.server.services.component_registry_services.exception_remapping_component_registry_service import (
    ExceptionRemappingComponentRegistryService,
)
from consortium.server.services.events_service import EventsService


class EventHookRegistryService(
    ExceptionRemappingComponentRegistryService[BaseEventHook, EventHookLoadingError],
):
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP = {
        comp_excs.ComponentProjectManifestFileNotFoundError: EventHookProjectManifestFileNotFoundError,
        comp_excs.InvalidComponentProjectManifestFileJSONError: InvalidEventHookProjectManifestFileJSONError,
        comp_excs.InvalidComponentProjectManifestFileSchemaError: InvalidEventHookProjectManifestFileSchemaError,
        comp_excs.InvalidComponentProjectPyProjectFileError: InvalidEventHookProjectPyProjectFileError,
        comp_excs.InvalidComponentProjectPyProjectFileTOMLError: InvalidEventHookProjectPyProjectFileTOMLError,
        comp_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidEventHookProjectPyProjectFileDependencyError,
        comp_excs.ComponentProjectEntryPointModuleNotFoundError: EventHookProjectEntryPointModuleNotFoundError,
        comp_excs.ComponentProjectSymbolNotFoundError: EventHookProjectSymbolNotFoundError,
        comp_excs.ComponentProjectInterfaceError: EventHookProjectInterfaceError,
        comp_excs.IncompatibleComponentFrameworkVersionError: IncompatibleEventHookFrameworkVersionError,
        comp_excs.InternalComponentProjectError: InternalEventHookProjectError,
        comp_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_excs.ComponentDependsOnInvalidComponentDependencyError: EventHookDependsOnInvalidComponentDependencyError,
        comp_excs.ComponentNotFoundError: EventHookNotFoundError,
        comp_excs.ComponentAlreadyRegisteredError: EventHookAlreadyRegisteredError,
        comp_excs.DuplicateComponentLabelError: DuplicateEventHookLabelError,
    }
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "event_hook_project_folder",
        "component_file": "event_hook_file",
        "component_symbol": "event_hook_symbol",
        "component_str": "event_hook_str",
        "component_id": "event_hook_id",
    }

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

    def _get_component_project_folder(self, component: BaseEventHook) -> pathlib.Path:
        return component.event_hook_project_folder

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
