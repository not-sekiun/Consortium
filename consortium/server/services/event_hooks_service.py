import pathlib
import uuid

from loguru import logger

from consortium.framework._core.framework_exceptions.event_hooks_framework_exceptions import (
    EventHooksFrameworkError,
)
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    EventHookLoadingError,
    EventHooksServiceError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.component_loader_services.event_hook_loader_service import (
    EventHookLoaderService,
)
from consortium.server.services.component_registry_services.event_hook_registry_service import (
    EventHookRegistryService,
)
from consortium.server.services.events_service import EventsService
from consortium.server.services.paths_service import PathsService
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
)


class EventHooksService:
    def __init__(
        self,
        events_service: EventsService,
        release_service: ReleaseService,
        paths_service: PathsService,
    ) -> None:
        self._event_hooks_directory = paths_service.event_hooks_directory
        self._events_service = events_service
        self._event_hook_loader_service = EventHookLoaderService(
            paths_service=paths_service,
            release_service=release_service,
        )
        self._event_hook_registry_service = EventHookRegistryService(
            component_loader_service=self._event_hook_loader_service,
            component_framework_directory=self._event_hooks_directory,
            events_service=events_service,
        )
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Event Hooks Service"

    def __repr__(self) -> str:
        return "EventHooksService()"

    @log_and_propagate_error_on_service_method
    def get_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook | None:
        """Instantiates an event hook from a project folder without registering it.

        Disabled event hooks (as indicated by `enabled: false` in their `manifest.json`)
        are not instantiated unless `ignore_enabled_event_hook_flag` is `True`.

        Args:
            event_hook_project_folder: Path to the directory containing
                the event hook project files and `manifest.json`.
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            The instantiated event hook, or `None` if the event hook is disabled and
            the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the event hook is
                incompatible with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs while
                loading the event hook.
        """
        event_hook = self._event_hook_registry_service.get_component_from_component_project_folder(
            component_project_folder=event_hook_project_folder,
            ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
        )
        if event_hook is None:
            self._logger.debug(
                "Skipped retrieving event hook from '{}' because it was disabled."
                "Either enable it in its manifest or force retrieve it by setting the "
                "`ignore_enabled_event_hook_flag` to `True`.",
                str(event_hook_project_folder),
            )
        else:
            self._logger.debug(
                "Retrieved event hook {} from event hook project folder: {}",
                repr(event_hook),
                str(event_hook_project_folder),
            )
        return event_hook

    @log_and_propagate_error_on_service_method
    def get_event_hooks_from_event_hook_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> tuple[
        list[BaseEventHook],
        list[pathlib.Path],
        list[tuple[pathlib.Path, EventHookLoadingError]] | None,
    ]:
        """Recursively scans a directory for event hook project folders and instantiates them.

        Disabled event hooks (as indicated by `enabled: false` in their `manifest.json`)
        are skipped unless `ignore_enabled_event_hook_flag` is `True`.

        Args:
            directory: The directory to scan for event hook project
                folders.
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled`
                check in each event hook's manifest. Defaults to `False`.

        Returns:
            A three-element tuple: (1) a list of successfully instantiated event
            hooks, (2) a list of paths skipped because the event hook was disabled,
            and (3) a list of `(path, error)` tuples for event hooks that failed to
            load.
        """
        retrieved, skipped, errored = (
            self._event_hook_registry_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
            )
        )
        self._logger.debug(
            "Retrieved event hooks from '{}' ({} event hook(s) retrieved, {} event hook(s) "
            "skipped, {} event hook(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(errored),
        )
        return (
            retrieved,
            skipped,
            errored,
        )

    @log_and_propagate_error_on_service_method
    def register_event_hook(self, event_hook: BaseEventHook) -> BaseEventHook:
        """Registers an already-instantiated event hook with the service.

        Args:
            event_hook: The event hook instance to register.

        Returns:
            The registered event hook instance.

        Raises:
            ComponentAlreadyRegisteredError: If an event hook with the same ID is
                already registered.
            DuplicateComponentLabelError: If an event hook with the same label is
                already registered.
        """
        self._event_hook_registry_service.register_component(
            component=event_hook,
        )
        self._logger.debug("Registered event hook: {!r}", event_hook)
        return event_hook

    @log_and_propagate_error_on_service_method
    def register_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook | None:
        """Instantiates and registers an event hook from a project folder.

        Disabled event hooks are skipped unless `ignore_enabled_event_hook_flag` is
        `True`.

        Args:
            event_hook_project_folder: Path to the directory containing
                the event hook project files and `manifest.json`.
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            The registered event hook instance, or `None` if the
                event hook is disabled and the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the event hook is
                incompatible with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs while
                loading the event hook.
            ComponentAlreadyRegisteredError: If an event hook with the same ID is
                already registered.
            DuplicateComponentLabelError: If an event hook with the same label is
                already registered.
        """
        event_hook = self._event_hook_registry_service.register_component_from_component_project_folder(
            component_project_folder=event_hook_project_folder,
            ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
        )
        if event_hook is None:
            self._logger.warning(
                "Skipped registering event hook from '{}' because it was disabled. Either "
                "enable it in its manifest or force register it by setting the "
                "`ignore_enabled_event_hook_flag` to `True`.",
                str(event_hook_project_folder),
            )
        else:
            self._logger.info("Registered event hook: {}", event_hook)
            self._logger.debug("Registered event hook: {!r}", event_hook)
        return event_hook

    @log_and_propagate_error_on_service_method
    async def load_event_hook(self, event_hook: BaseEventHook) -> BaseEventHook:
        """Registers and activates an already-instantiated event hook.

        Args:
            event_hook: The event hook instance to load.

        Returns:
            The loaded event hook instance.

        Raises:
            ComponentAlreadyRegisteredError: If an event hook with the same ID is
                already registered.
        """
        event_hook = await self._event_hook_registry_service.load_component(
            component=event_hook,
        )
        self._logger.debug("Loaded event hook: {!r}", event_hook)
        return event_hook

    @log_and_propagate_error_on_service_method
    async def load_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: pathlib.Path,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook | None:
        """Instantiates, registers, and activates an event hook from a project folder.

        Disabled event hooks are skipped unless `ignore_enabled_event_hook_flag` is
        `True`.

        Args:
            event_hook_project_folder: Path to the directory containing
                the event hook project files and `manifest.json`.
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            The loaded event hook instance, or `None` if the event hook is disabled and
            the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the event hook is
                incompatible with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs while
                loading the event hook.
        """
        event_hook = await self._event_hook_registry_service.load_component_from_component_project_folder(
            component_project_folder=event_hook_project_folder,
            ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
        )
        if event_hook is None:
            self._logger.warning(
                "Skipped loading event hook from '{}' because it was disabled. Either "
                "enable it in its manifest or force load it by setting the "
                "`ignore_enabled_event_hook_flag` to `True`.",
                str(event_hook_project_folder),
            )
        else:
            self._logger.info("Loaded event hook: {}", event_hook)
            self._logger.debug("Loaded event hook: {!r}", event_hook)
        return event_hook

    @log_and_propagate_error_on_service_method
    async def unload_event_hook_by_event_hook_id(
        self,
        event_hook_id: str | uuid.UUID,
    ) -> None:
        """Deactivates and deregisters a loaded event hook by its ID.

        Args:
            event_hook_id: The ID of the event hook to unload.

        Raises:
            ComponentNotFoundError: If no event hook with the given ID is registered.
        """
        event_hook = (
            await self._event_hook_registry_service.unload_component_by_component_id(
                component_id=event_hook_id,
            )
        )
        self._logger.info("Unloaded event hook: {}", event_hook)
        self._logger.debug("Unloaded event hook: {!r}", event_hook)

    @log_and_propagate_error_on_service_method
    async def reload_event_hook_by_event_hook_id(
        self,
        event_hook_id: str | uuid.UUID,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> BaseEventHook:
        """Unloads and reloads an event hook from its original project folder.

        If the event hook is disabled after reload and `ignore_enabled_event_hook_flag`
        is `False`, the event hook will only be unloaded, not reloaded.

        Args:
            event_hook_id: The ID of the event hook to reload.
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled` check
                in the manifest during reload. Defaults to `False`.

        Returns:
            The reloaded event hook instance, or `None` if the event hook was disabled
            and the enabled check was not overridden.

        Raises:
            ComponentNotFoundError: If no event hook with the given ID is registered.
        """
        event_hook = (
            await self._event_hook_registry_service.reload_component_by_component_id(
                component_id=event_hook_id,
                ignore_enabled_component_flag=ignore_enabled_event_hook_flag,
            )
        )
        if event_hook is None:
            self._logger.warning(
                "Previously loaded event hook with ID '{}' could not be reloaded "
                "because it is currently disabled. As a result, the event hook has "
                "only been unloaded but not loaded back. Either enable it in its "
                "manifest and load it again or force load it by setting the "
                "`ignore_enabled_event_hook_flag` to `True`.",
                event_hook_id,
            )
        else:
            self._logger.info("Reloaded event hook: {}", event_hook)
            self._logger.debug("Reloaded event hook: {!r}", event_hook)
        return event_hook

    @log_and_propagate_error_on_service_method
    async def load_framework_event_hooks(
        self,
        ignore_enabled_event_hook_flag: bool = False,
    ) -> None:
        """Scans the framework's event hooks directory and loads all enabled event hooks.

        Disabled event hooks and those that fail to load are logged and skipped without
        aborting the overall load.

        Args:
            ignore_enabled_event_hook_flag: When `True`, bypasses the `enabled`
                check in each event hook's manifest. Defaults to `False`.

        """
        self._logger.info("Loading framework event hooks...")
        retrieved, skipped, errored = (
            self.get_event_hooks_from_event_hook_project_folder_directories(
                directory=self._event_hooks_directory,
                ignore_enabled_event_hook_flag=ignore_enabled_event_hook_flag,
            )
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading plugin from '{}' because it was disabled",
                str(path),
            )
        if errored:
            for _, error in errored:
                self._logger.error(
                    "- {}",
                    str(error),
                )

        # TODO: Build in topological sorting after figuring out how to implement the
        #  dependency system?
        failed_to_load = 0
        for event_hook in retrieved:
            try:
                await self.load_event_hook(event_hook=event_hook)
                self._logger.success("- Loaded event hook: {}", event_hook)
                self._logger.debug("- Loaded event hook: {!r}", event_hook)
            except (EventHooksFrameworkError, EventHooksServiceError) as exc:
                failed_to_load += 1
                self._logger.error("- {}", exc)

        self._logger.info(
            "Loaded event hooks from '{}' ({} event hook(s) loaded, {} event "
            "hook(s) skipped, {} event hook(s) failed to load)",
            str(self._event_hooks_directory),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    def unload_framework_event_hooks(self) -> None:
        """Unloads all event hooks that were loaded from the framework's event hooks directory."""
        self._logger.info("Unloading framework event hooks...")
        unloaded_event_hooks = 0
        for event_hook in self.get_all_event_hooks():
            if event_hook.event_hook_project_folder.resolve().relative_to(
                self._event_hooks_directory.resolve()
            ):
                self.unload_event_hook_by_event_hook_id(
                    event_hook_id=str(event_hook.event_hook_id),
                )
                unloaded_event_hooks += 1

        self._logger.info(
            "Unloaded framework event hooks ({} event hook(s) unloaded)",
            unloaded_event_hooks,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_event_hooks(
        self,
    ) -> None:
        """Unloads all framework event hooks then reloads them from the event hooks directory."""
        self._logger.info("Reloading framework event hooks...")
        self.unload_framework_event_hooks()
        await self.load_framework_event_hooks()
        self._logger.info("Reloaded framework event hooks")

    @log_and_propagate_error_on_service_method
    def get_event_hook_by_event_hook_id(
        self, event_hook_id: str | uuid.UUID
    ) -> BaseEventHook:
        """Returns a loaded event hook by its ID.

        Args:
            event_hook_id: The ID of the event hook to retrieve.

        Returns:
            The requested event hook.

        Raises:
            ComponentNotFoundError: If no event hook with the given ID is registered.
        """
        event_hook = self._event_hook_registry_service.get_component_by_component_id(
            component_id=event_hook_id,
        )
        self._logger.debug(f"Retrieved event hook: {event_hook!r}")
        return event_hook

    @log_and_propagate_error_on_service_method
    def get_all_event_hooks(self) -> list[BaseEventHook]:
        """Returns all currently loaded event hooks.

        Returns:
            A list of all loaded event hooks. Empty if none are
                loaded.
        """
        event_hooks = self._event_hook_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all event hooks ({} event hook(s) retrieved)",
            len(event_hooks),
        )
        return event_hooks

    @log_and_propagate_error_on_service_method
    def get_all_event_types(self) -> list[EventType]:
        """Returns all supported event types.

        Returns:
            A list of all values from the `EventType` enum.
        """
        event_types = list(EventType)
        self._logger.debug(
            "Retrieved all event types ({} event type(s) retrieved)",
            event_types,
        )
        return event_types

    @log_and_propagate_error_on_service_method
    async def trigger_event(self, event: Event) -> None:
        """Triggers an event, invoking every handler registered for its type.

        This is a convenience wrapper around `EventsService.trigger_event` for callers
        already working with the event hooks service. It delegates entirely to the
        events service so event hooks and any other registered handlers (for example,
        websocket subscribers) are notified through the same code path.

        Args:
            event: The event to trigger.

        Raises:
            ExceptionGroup: If one or more registered handlers raise exceptions. Event
                hooks that raise `EventHookTriggerError` from `on_triggered()` are
                represented in the group as the consortium-level `EventHookTriggerError`.
        """
        self._logger.debug("Triggered event: {}", event)
        await self._events_service.trigger_event(
            event_type=event.event_type,
            message=event.message,
            data=event.data,
        )
