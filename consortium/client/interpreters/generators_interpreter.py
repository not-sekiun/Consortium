from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML

from consortium.client.client_websockets_events_api import EventHandler
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands import (
    GENERATORS_INTERPRETER_COMMANDS,
    AgentTemplateListCommand,
    GeneratorListCommand,
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

COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "generators"
] + GENERATORS_INTERPRETER_COMMANDS


class GeneratorsInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
        prompt: str | ANSI | HTML | list[tuple[str, str]] | None = None,
        commands: list[BaseCommand] | None = None,
    ):
        if prompt is None:
            prompt = HTML(
                "<b>Consortium (<ansigreen>Generators</ansigreen>)\n> </b>",
            )
        if commands is None:
            commands = COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS

        # Runtime data the autocomplete sentinels of this interpreter's commands are
        # resolved against
        self._all_agent_generators: list[dict[str, Any]] = []
        self._all_agent_templates: list[dict[str, Any]] = []
        self._all_payloads: list[dict[str, Any]] = []

        super().__init__(
            prompt=prompt,
            commands=commands,
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def _get_all_agent_generators_and_agent_templates(self):
        all_agent_generators = (
            await self.client_session.rest_api.get_all_agent_generators()
        )
        all_agent_templates = (
            await self.client_session.rest_api.get_all_agent_templates()
        )
        return all_agent_generators, all_agent_templates

    async def _get_all_payloads(self) -> list[dict[str, Any]]:
        return await self.client_session.rest_api.get_all_payloads()

    def get_autocomplete_resolutions(self) -> AutocompleteResolutions:
        return super().get_autocomplete_resolutions() | {
            Autocomplete.AGENT_GENERATOR_ID: [
                agent_generator["agent_generator_id"]
                for agent_generator in self._all_agent_generators
            ],
            # Every agent generator ID additionally carries the parameter names of that
            # specific agent generator underneath it
            Autocomplete.AGENT_GENERATOR_ID_WITH_PARAMETERS: {
                agent_generator["agent_generator_id"]: dict.fromkeys(
                    agent_generator["parameters"],
                )
                for agent_generator in self._all_agent_generators
            },
            Autocomplete.AGENT_TEMPLATE_ID: [
                agent_template["agent_template_id"]
                for agent_template in self._all_agent_templates
            ],
            Autocomplete.PAYLOAD_ID: [
                payload["resource_id"] for payload in self._all_payloads
            ],
        }

    def _initialize_autocomplete(
        self,
        all_agent_generators: list[dict[str, Any]],
        all_agent_templates: list[dict[str, Any]],
        all_payloads: list[dict[str, Any]],
    ) -> None:
        self._all_agent_generators = all_agent_generators
        self._all_agent_templates = all_agent_templates
        self._all_payloads = all_payloads
        self.refresh_autocomplete()

    async def _agent_generator_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        (
            all_agent_generators,
            all_agent_templates,
        ) = await self._get_all_agent_generators_and_agent_templates()
        all_payloads = await self._get_all_payloads()
        self._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
            all_payloads=all_payloads,
        )

    async def _payload_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        (
            all_agent_generators,
            all_agent_templates,
        ) = await self._get_all_agent_generators_and_agent_templates()
        all_payloads = await self._get_all_payloads()
        self._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
            all_payloads=all_payloads,
        )

    # Single source of truth for this interpreter's event subscriptions, so that setup
    # and teardown can never drift apart.
    def _get_event_handlers(self) -> dict[str, EventHandler]:
        return {
            "AGENT_GENERATOR_CREATED": (
                self._agent_generator_created_or_removed_event_handler
            ),
            "AGENT_GENERATOR_REMOVED": (
                self._agent_generator_created_or_removed_event_handler
            ),
            "PAYLOAD_CREATED": self._payload_created_or_removed_event_handler,
            "PAYLOAD_DELETED": self._payload_created_or_removed_event_handler,
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

    @staticmethod
    def _list_all_agent_generators_and_agent_templates(
        all_agent_generators: list[dict[str, Any]],
        all_agent_templates: list[dict[str, Any]],
    ) -> None:
        GeneratorListCommand._list_all_agent_generators(
            all_agent_generators=all_agent_generators,
        )
        AgentTemplateListCommand._list_all_agent_templates(
            all_agent_templates=all_agent_templates,
        )

    async def on_enter(self) -> None:
        (
            all_agent_generators,
            all_agent_templates,
        ) = await self._get_all_agent_generators_and_agent_templates()
        all_payloads = await self._get_all_payloads()
        self._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
            all_payloads=all_payloads,
        )
        await self._setup_event_handlers()
        self._list_all_agent_generators_and_agent_templates(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
        )

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.client_session.websockets_api.connected:
            await self._teardown_event_handlers()
