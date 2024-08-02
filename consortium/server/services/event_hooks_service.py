import importlib
import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.framework.base_event_hook import BaseEventHook
from consortium.server.exceptions.framework_exceptions.event_hooks_framework_exceptions import (
    EventHooksFrameworkError,
)
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    EventHookLoadingError,
    EventHookNotFoundError,
    EventHookProjectEventHookFileNotFoundError,
    EventHookProjectInterfaceError,
    EventHookProjectManifestFileNotFoundError,
    EventHookProjectSymbolNotFoundError,
    InternalEventHookProjectError,
    InvalidEventHookProjectManifestFileJSONError,
    InvalidEventHookProjectManifestFileSchemaError,
)
from consortium.server.objects.event_objects import Event, EventType
from consortium.server.server_config import (
    CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH,
    CONSORTIUM_HOME_DIRECTORY_PATH,
)
from consortium.server.services.events_service import EventsService


class EventHooksService:
    def __init__(self, events_service: EventsService):
        self._event_hooks = {}
        self._events_service = events_service
        self.event_hooks_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.event_hooks_service_logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Consortium Event Hooks Service"

    def __repr__(self) -> str:
        return "EventHooksService()"

    def get_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: Path,
    ) -> BaseEventHook:
        event_hook_project_manifest_file_path = (
            event_hook_project_folder / "event_hook_project_manifest.json"
        )
        event_hook_project_manifest_json_schema = {
            "type": "object",
            "properties": {
                "event_hook": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                    "required": ["filepath", "symbol"],
                },
            },
            "required": [
                "event_hook",
            ],
        }

        # Check if manifest file exists and follows the correct json schema.
        try:
            with event_hook_project_manifest_file_path.open(
                "r",
            ) as event_hook_project_manifest_file:
                event_hook_project_manifest_json = json.load(
                    event_hook_project_manifest_file,
                )
                jsonschema.validate(
                    event_hook_project_manifest_json,
                    event_hook_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise EventHookProjectManifestFileNotFoundError(
                event_hook_project_folder=str(event_hook_project_folder),
            )
        except json.JSONDecodeError:
            raise InvalidEventHookProjectManifestFileJSONError(
                event_hook_project_folder=str(event_hook_project_folder),
            )
        except jsonschema.ValidationError as exc:
            raise InvalidEventHookProjectManifestFileSchemaError(
                event_hook_project_folder=str(event_hook_project_folder),
                json_schema_error_message=exc.message,
            )

        # Check for valid project folder structure as specified by the manifest file.
        event_hook_file = event_hook_project_folder / Path(
            event_hook_project_manifest_json["event_hook"]["filepath"],
        )
        event_hook_symbol = event_hook_project_manifest_json["event_hook"]["symbol"]

        if not event_hook_file.exists():
            raise EventHookProjectEventHookFileNotFoundError(
                event_hook_file=str(event_hook_file),
                event_hook_project_folder=str(event_hook_project_folder),
            )

        # Check for valid symbol names in the required event hook project file.
        event_hook_module_path = ".".join(
            event_hook_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]

        try:
            event_hook_module = importlib.import_module(event_hook_module_path)
            event_hook_class = getattr(
                event_hook_module,
                event_hook_symbol,
            )
        except AttributeError:
            raise EventHookProjectSymbolNotFoundError(
                symbol_name=event_hook_symbol,
                event_hook_file=str(event_hook_file),
                event_hook_project_folder=str(event_hook_project_folder),
            )
        except EventHooksFrameworkError as exc:
            raise exc from None
        except Exception as exc:
            raise InternalEventHookProjectError(
                event_hook_project_folder=str(event_hook_project_folder),
                internal_error_message=str(exc),
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(event_hook_class, BaseEventHook):
            raise EventHookProjectInterfaceError(
                event_hook_symbol=event_hook_symbol,
                event_hook_project_folder=str(event_hook_project_folder),
            )

        try:
            event_hook_object = event_hook_class()
        except EventHooksFrameworkError as exc:
            raise exc from None
        except Exception as exc:
            raise InternalEventHookProjectError(
                event_hook_project_folder=str(event_hook_project_folder),
                internal_error_message=str(exc),
            )

        self.event_hooks_service_logger.debug(
            f"Retrieved event hook {event_hook_object!r} from event hook project "
            f"folder: {event_hook_project_folder}",
        )
        return event_hook_object

    def load_framework_event_hooks(self) -> None:
        self.event_hooks_service_logger.info(f"Loading framework event hooks...")

        # Recursively search through the event hooks directory to find all event hook
        # project folders.
        number_of_loaded_event_hooks = 0
        for path in CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH.rglob("*"):
            if path.name != "event_hook_project_manifest.json":
                continue

            try:
                self.load_event_hook_from_event_hook_project_folder(
                    event_hook_project_folder=path.parent,
                )
            except EventHookLoadingError as exc:
                self.event_hooks_service_logger.error(exc)
                continue
            number_of_loaded_event_hooks += 1

        self.event_hooks_service_logger.info(
            f"Loaded framework event hooks ({number_of_loaded_event_hooks} event "
            "hook(s) loaded).",
        )

    def unload_framework_event_hooks(self) -> None:
        self.event_hooks_service_logger.info(f"Unloading framework event hooks...")

        number_of_unloaded_event_hooks = 0
        for event_hook in self.get_all_event_hooks():
            if (
                event_hook.event_hook_project_folder.parent
                == CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH
            ):
                self.unload_event_hook_by_event_hook_id(
                    event_hook_id=str(event_hook.event_hook_id),
                )
                number_of_unloaded_event_hooks += 1

        self.event_hooks_service_logger.info(
            f"Unloaded framework event hooks ({number_of_unloaded_event_hooks} event "
            "hooks(s) unloaded).",
        )

    async def reload_framework_event_hooks(
        self,
    ) -> None:
        self.event_hooks_service_logger.info(f"Reloading framework event hooks...")
        self.unload_framework_event_hooks()
        self.load_framework_event_hooks()
        self.event_hooks_service_logger.info(f"Reloaded framework event hooks.")

    def load_event_hook_from_event_hook_project_folder(
        self,
        event_hook_project_folder: Path,
    ) -> BaseEventHook:
        event_hook = self.get_event_hook_from_event_hook_project_folder(
            event_hook_project_folder,
        )
        self._event_hooks[str(event_hook.event_hook_id)] = event_hook
        for event_type in event_hook.event_types:
            self._events_service.register_event_handler_to_event_type(
                event_type=event_type,
                event_handler=event_hook.on_event_hook_triggered,
            )
        self.event_hooks_service_logger.info(f"Loaded event hook: {event_hook}")
        self.event_hooks_service_logger.debug(f"Loaded event hook: {event_hook!r}")
        return event_hook

    def unload_event_hook_by_event_hook_id(
        self,
        event_hook_id: str,
    ) -> BaseEventHook:
        try:
            event_hook = self._event_hooks.pop(event_hook_id)
        except KeyError:
            raise EventHookNotFoundError(
                event_hook_id=event_hook_id,
            )

        for event_type in event_hook.event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=event_hook.on_event_hook_triggered,
            )

        self.event_hooks_service_logger.info(f"Unloaded event hook: {event_hook}")
        self.event_hooks_service_logger.debug(f"Unloaded event hook: {event_hook!r}")
        return event_hook

    def reload_event_hook_by_event_hook_id(self, event_hook_id: str) -> BaseEventHook:
        old_event_hook = self.unload_event_hook_by_event_hook_id(event_hook_id)
        event_hook_project_folder = old_event_hook.event_hook_project_folder
        new_event_hook = self.load_event_hook_from_event_hook_project_folder(
            event_hook_project_folder,
        )
        self.event_hooks_service_logger.info(f"Reloaded event hook: {new_event_hook}")
        self.event_hooks_service_logger.debug(
            f"Reloaded event hook: {new_event_hook!r}",
        )
        return new_event_hook

    def get_event_hook_by_event_hook_id(self, event_hook_id: str) -> BaseEventHook:
        try:
            event_hook = self._event_hooks[event_hook_id]
        except KeyError:
            raise EventHookNotFoundError(
                event_hook_id=event_hook_id,
            )

        self.event_hooks_service_logger.debug(f"Retrieved event hook: {event_hook!r}")
        return event_hook

    def get_all_event_hooks(self) -> list[BaseEventHook]:
        self.event_hooks_service_logger.debug(
            f"Retrieved all event hooks ({len(self._event_hooks)} event hook(s) "
            "retrieved).",
        )
        return list(self._event_hooks.values())

    @staticmethod
    def get_all_event_types() -> list[str]:
        return [event_type for event_type in EventType]

    def trigger_event(self, event: Event):
        for event_hook in self._event_hooks.values():
            if event.event_type in event_hook.event_types:
                event_hook.on_event_hook_triggered(event)
