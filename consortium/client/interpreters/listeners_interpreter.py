from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML

from consortium.client.client_websockets_events_api import EventHandler
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.listeners_interpreter_commands import (
    LISTENERS_INTERPRETER_COMMANDS,
    ListenerListCommand,
    ListenerTemplateListCommand,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.autocompletes import (
    Autocomplete,
    AutocompleteResolutions,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "listeners"
] + LISTENERS_INTERPRETER_COMMANDS


class ListenersInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
        prompt: str | ANSI | HTML | list[tuple[str, str]] | None = None,
        commands: list[BaseCommand] | None = None,
    ):
        if prompt is None:
            prompt = HTML(
                "<b>Consortium (<ansiblue>Listeners</ansiblue>)\n> </b>",
            )
        if commands is None:
            commands = COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS

        # Runtime data the autocomplete sentinels of this interpreter's commands are
        # resolved against
        self._all_listeners: list[dict[str, Any]] = []
        self._all_listener_templates: list[dict[str, Any]] = []

        super().__init__(
            prompt=prompt,
            commands=commands,
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def _get_all_listeners_and_listener_templates(self):
        all_listeners = await self.client_session.rest_api.get_all_listeners()
        all_listener_templates = (
            await self.client_session.rest_api.get_all_listener_templates()
        )
        return all_listeners, all_listener_templates

    def _get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return super()._get_autocomplete_resolutions() | {
            Autocomplete.LISTENER_ID: [
                listener["listener_id"] for listener in self._all_listeners
            ],
            # Every listener ID additionally carries the parameter names of that
            # specific listener underneath it
            Autocomplete.LISTENER_ID_WITH_PARAMETERS: {
                listener["listener_id"]: dict.fromkeys(listener["parameters"])
                for listener in self._all_listeners
            },
            Autocomplete.LISTENER_TEMPLATE_ID: [
                listener_template["listener_template_id"]
                for listener_template in self._all_listener_templates
            ],
        }

    def _initialize_autocomplete(
        self,
        all_listeners: list[dict[str, Any]],
        all_listener_templates: list[dict[str, Any]],
    ) -> None:
        self._all_listeners = all_listeners
        self._all_listener_templates = all_listener_templates
        self.refresh_autocomplete()

    @staticmethod
    def _list_all_listeners_and_listener_templates(
        all_listeners: list[dict[str, Any]],
        all_listener_templates: list[dict[str, Any]],
    ) -> None:
        ListenerListCommand._list_all_listeners(
            all_listeners=all_listeners,
        )
        ListenerTemplateListCommand._list_all_listener_templates(
            all_listener_templates=all_listener_templates,
        )

    # We don't actually care about the event data so we just ignore it. We just need to
    # know a change happened so that we can update the autocompleter.
    async def _listener_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        (
            all_listeners,
            all_listener_templates,
        ) = await self._get_all_listeners_and_listener_templates()
        self._initialize_autocomplete(
            all_listeners=all_listeners,
            all_listener_templates=all_listener_templates,
        )

    # Single source of truth for this interpreter's event subscriptions, so that setup
    # and teardown can never drift apart.
    def _get_event_handlers(self) -> dict[str, EventHandler]:
        return {
            "LISTENER_CREATED": self._listener_created_or_removed_event_handler,
            "LISTENER_REMOVED": self._listener_created_or_removed_event_handler,
        }

    async def _setup_event_handlers(self) -> None:
        await self.client_session.websockets_api.subscribe_to_events(
            event_handlers=self._get_event_handlers(),
        )
        await self.client_session.websockets_api.start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.client_session.websockets_api.stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.client_session.websockets_api.unsubscribe_from_events(
            event_handlers=self._get_event_handlers(),
        )

    async def on_enter(self) -> None:
        (
            all_listeners,
            all_listener_templates,
        ) = await self._get_all_listeners_and_listener_templates()
        self._initialize_autocomplete(
            all_listeners=all_listeners,
            all_listener_templates=all_listener_templates,
        )
        await self._setup_event_handlers()
        self._list_all_listeners_and_listener_templates(
            all_listeners=all_listeners,
            all_listener_templates=all_listener_templates,
        )

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.client_session.websockets_api.connected:
            await self._teardown_event_handlers()
