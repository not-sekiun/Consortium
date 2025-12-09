import pathlib
import uuid

import consortium.server.exceptions.service_exceptions.component_service_exceptions as comp_ldr_svc_excs
from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicateEventHookLabelError,
    EventHookAlreadyRegisteredError,
    EventHookDependsOnInvalidComponentDependencyError,
    EventHookLoadingError,
    EventHookNotFoundError,
    EventHookProjectEventHookFileNotFoundError,
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
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: EventHookProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidEventHookProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidEventHookProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidEventHookProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidEventHookProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectComponentFileNotFoundError: EventHookProjectEventHookFileNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: EventHookProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: EventHookProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatibleEventHookFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalEventHookProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: EventHookDependsOnInvalidComponentDependencyError,
        comp_ldr_svc_excs.ComponentNotFoundError: EventHookNotFoundError,
        comp_ldr_svc_excs.ComponentAlreadyRegisteredError: EventHookAlreadyRegisteredError,
        comp_ldr_svc_excs.DuplicateComponentLabelError: DuplicateEventHookLabelError,
    }
    _EXCEPTION_KWARGS_MAP = {
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
                event_handler=component.on_event_hook_triggered,
            )
        try:
            await component.on_event_hook_setup()
        except Exception as exc:
            raise EventHookSetupError(
                event_hook_str=str(component),
                error_message=str(exc),
            ) from exc
        return component

    async def _component_unload_procedure(
        self,
        component: BaseEventHook,
        context: dict,
    ) -> BaseEventHook:
        try:
            await component.on_event_hook_teardown()
        except Exception as exc:
            raise EventHookTeardownError(
                event_hook_str=str(component),
                error_message=str(exc),
            ) from None
        for event_type in component.event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=component.on_event_hook_triggered,
            )
        return component
