import pathlib

from loguru import logger

import consortium.server.exceptions.service_exceptions.component_loader_service_exceptions as comp_ldr_svc_excs
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EventHooksFrameworkError,
)
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    EventHookAlreadyRegisteredError,
    EventHookDependsOnInvalidComponentDependencyError,
    EventHookLoadingError,
    EventHookNotFoundError,
    EventHookProjectEventHookFileNotFoundError,
    EventHookProjectInterfaceError,
    EventHookProjectManifestFileNotFoundError,
    EventHookProjectSymbolNotFoundError,
    EventHookSetupError,
    EventHooksServiceError,
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
from consortium.server.server_config import CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH
from consortium.server.services.component_loader_services.event_hook_loader_service import (
    EventHookLoaderService,
)
from consortium.server.services.events_service import EventsService


class EventHooksService:
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
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "event_hook_project_folder",
        "component_file": "event_hook_file",
        "component_symbol": "event_hook_symbol",
        "component_str": "event_hook_str",
        "component_id": "event_hook_id",
    }

    def __init__(self, events_service: EventsService):
        self._event_hooks = {}
        self._events_service = events_service
        self._event_hook_loader_service = EventHookLoaderService()
        self.logger = logger.bind(
            logger_name=str(self),
        )
        self.logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Event Hooks Service"

    def __repr__(self) -> str:
        return "EventHooksService()"

    def get_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook | None:
        try:
            event_hook = self._event_hook_loader_service.get_component_from_component_project_folder(
                component_project_folder=event_hook_project_folder,
                ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
            )
        except (
            comp_ldr_svc_excs.ComponentLoadingError,
            comp_ldr_svc_excs.ComponentDependencyError,
        ) as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=self._EXCEPTION_MAP,
                exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
            ) from None
        if event_hook is None:
            self.logger.debug(
                "Skipped loading event hook from '{}' because it was disabled.",
                str(event_hook_project_folder),
            )
        else:
            self.logger.debug(
                "Retrieved event hook {} from event hook project folder: {}",
                repr(event_hook),
                str(event_hook_project_folder),
            )
        return event_hook

    def get_event_hooks_from_event_hook_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> tuple[
        list[BaseEventHook],
        list[pathlib.Path],
        list[tuple[pathlib.Path, EventHookLoadingError]] | None,
    ]:
        """
        Retrieves all event hooks from the specified directory containing event hook project folders.

        Event Hooks that are specified to be disabled in their `manifest.json` will not be
        loaded unless `ignore_enabled_event_hook_flag` is set to `True`. Valid event hooks are
        instantiated and returned.

        Args:
            directory (pathlib.Path): The path of the directory containing event hook
                project folders.
            ignore_enabled_event_hook_flag (bool): If `True`, the method bypasses the
                enabled state check in the event hook project manifests.

        Returns:
            tuple[list[BaseEventHook], list[pathlib.Path], list[tuple[pathlib.Path, EventHookLoadingError]] | None]:
                A tuple containing three elements:
                1. A list of successfully retrieved event hook instances.
                2. A list of pathlib.Path objects representing the event hook project
                    folders that were skipped because the event hooks were disabled.
                3. A list of tuples, each containing a pathlib.Path object representing
                    the event hook project folder that failed to load and the corresponding
                    `EventHookLoadingError` exception.

        Raises:
            See [get_event_hook_from_event_hook_project_folder][consortium.server.services.event_hooks_service.EventHooksService.get_event_hook_from_event_hook_project_folder]
            for possible exceptions raised during event hook retrieval.
        """
        retrieved, skipped, errored = (
            self._event_hook_loader_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
            )
        )
        remapped_errored = []
        for error_tuple in errored:
            error = error_tuple[1]
            # A configuration error will raise a EventHookConfigurationError which is not
            # a ComponentLoadingError, so we only remap ComponentLoadingErrors here.
            if isinstance(
                error,
                (
                    comp_ldr_svc_excs.ComponentLoadingError,
                    comp_ldr_svc_excs.ComponentDependencyError,
                ),
            ):
                remapped_errored.append(
                    (
                        error_tuple[0],
                        remap_exception(
                            original_exception=error,
                            original_kwargs=error.kwargs,
                            exception_map=self._EXCEPTION_MAP,
                            exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
                        ),
                    ),
                )
            else:
                remapped_errored.append(error_tuple)
        self.logger.debug(
            "Retrieved event hooks from '{}' ({} event hook(s) retrieved, {} event hook(s) "
            "skipped, {} event hook(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(remapped_errored),
        )
        return (
            retrieved,
            skipped,
            remapped_errored,
        )

    async def load_event_hook(self, event_hook: BaseEventHook) -> BaseEventHook:
        if str(event_hook.event_hook_id) in self._event_hooks:
            raise EventHookAlreadyRegisteredError(
                event_hook_str=str(event_hook),
                event_hook_id=str(event_hook.event_hook_id),
            )
        self._event_hooks[str(event_hook.event_hook_id)] = event_hook
        for event_type in event_hook.event_types:
            self._events_service.register_event_handler_to_event_type(
                event_type=event_type,
                event_handler=event_hook.on_event_hook_triggered,
            )
        try:
            await event_hook.on_event_hook_setup()
        except Exception as exc:
            raise EventHookSetupError(
                event_hook_str=str(event_hook),
                error_message=str(exc),
            ) from exc
        self.logger.debug(f"Loaded event hook: {event_hook!r}")
        return event_hook

    async def load_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook | None:
        event_hook = self.get_event_hook_from_event_hook_project_folder(
            event_hook_project_folder,
            ignore_enabled_event_hook_flag=ignore_enabled_event_hook_flag,
        )
        if event_hook is None:
            return None
        await self.load_event_hook(event_hook=event_hook)
        return event_hook

    async def unload_event_hook_by_event_hook_id(
        self,
        event_hook_id: str,
    ) -> None:
        event_hook = self.get_event_hook_by_event_hook_id(event_hook_id=event_hook_id)
        try:
            await event_hook.on_event_hook_teardown()
        except Exception as exc:
            raise EventHookTeardownError(
                event_hook_str=str(event_hook),
                error_message=str(exc),
            )
        self._event_hooks.pop(event_hook_id)
        for event_type in event_hook.event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=event_hook.on_event_hook_triggered,
            )
        self.logger.info(f"Unloaded event hook: {event_hook}")
        self.logger.debug(f"Unloaded event hook: {event_hook!r}")

    async def reload_event_hook_by_event_hook_id(
        self,
        event_hook_id: str,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook:
        event_hook = self.get_event_hook_by_event_hook_id(event_hook_id=event_hook_id)
        event_hook_project_folder = event_hook.event_hook_project_folder
        await self.unload_event_hook_by_event_hook_id(event_hook_id=event_hook_id)
        event_hook = await self.load_event_hook_from_event_hook_project_folder(
            event_hook_project_folder=event_hook_project_folder,
            ignore_enabled_event_hook_flag=ignore_enabled_event_hook_flag,
        )
        self.logger.info("Reloaded event hook: {}", event_hook)
        self.logger.debug("Reloaded event hook: {!r}", event_hook)
        return event_hook

    async def load_framework_event_hooks(
        self,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> None:
        self.logger.info("Loading framework event hooks...")
        retrieved, skipped, errored = (
            self.get_event_hooks_from_event_hook_project_folder_directories(
                directory=CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH,
                ignore_enabled_event_hook_flag=ignore_enabled_event_hook_flag,
            )
        )
        for path in skipped:
            self.logger.info(
                "├─ Skipped loading plugin from '{}' because it was disabled.",
                str(path),
            )
        if errored:
            for _, error in errored:
                self.logger.error(
                    "├─ {}",
                    str(error),
                )

        # TODO: Build in topological sorting after figuring out how to implement the
        #  dependency system?
        failed_to_load = 0
        for event_hook in retrieved:
            try:
                await self.load_event_hook(event_hook=event_hook)
                self.logger.success("├─ Loaded event hook: {}", event_hook)
                self.logger.debug("├─ Loaded event hook: {!r}", event_hook)
            except (EventHooksFrameworkError, EventHooksServiceError) as exc:
                failed_to_load += 1
                self.logger.error("├─ {}", exc)

        self.logger.info(
            "└─ Loaded event hooks from '{}' ({} event hook(s) loaded, {} event hook(s) "
            "skipped, {} event hook(s) failed to load).",
            str(CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    def unload_framework_event_hooks(self) -> None:
        self.logger.info("Unloading framework event hooks...")
        unloaded_event_hooks = 0
        for event_hook in self.get_all_event_hooks():
            if (
                event_hook.event_hook_project_folder.parent
                == CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH
            ):
                self.unload_event_hook_by_event_hook_id(
                    event_hook_id=str(event_hook.event_hook_id),
                )
                unloaded_event_hooks += 1

        self.logger.info(
            "Unloaded framework event hooks ({} event hook(s) unloaded).",
            unloaded_event_hooks,
        )

    async def reload_framework_event_hooks(
        self,
    ) -> None:
        self.logger.info(f"Reloading framework event hooks...")
        self.unload_framework_event_hooks()
        await self.load_framework_event_hooks()
        self.logger.info(f"Reloaded framework event hooks.")

    def get_event_hook_by_event_hook_id(self, event_hook_id: str) -> BaseEventHook:
        try:
            event_hook = self._event_hooks[event_hook_id]
        except KeyError:
            raise EventHookNotFoundError(
                event_hook_id=event_hook_id,
            )

        self.logger.debug(f"Retrieved event hook: {event_hook!r}")
        return event_hook

    def get_all_event_hooks(self) -> list[BaseEventHook]:
        self.logger.debug(
            "Retrieved all event hooks ({} event hook(s) retrieved).",
            len(self._event_hooks),
        )
        return list(self._event_hooks.values())

    @staticmethod
    def get_all_event_types() -> list[str]:
        return [event_type for event_type in EventType]

    def trigger_event(self, event: Event):
        for event_hook in self._event_hooks.values():
            if event.event_type in event_hook.event_types:
                event_hook.on_event_hook_triggered(event)
