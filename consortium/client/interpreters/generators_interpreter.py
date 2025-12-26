from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands import (
    GENERATORS_INTERPRETER_COMMANDS,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.repl_interface.interpreter import Interpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "generators"
] + GENERATORS_INTERPRETER_COMMANDS


class GeneratorsInterpreter(Interpreter):
    def __init__(
        self,
        client_session: ClientSession,
        prompt: str | ANSI | HTML | list[tuple[str, str]] | None = None,
        commands: list[BaseCommand] | None = None,
        context: dict[str, Any] | None = None,
    ):
        if prompt is None:
            prompt = HTML(
                "<b>Consortium (<ansigreen>Generators</ansigreen>) > </b>",
            )
        if commands is None:
            commands = COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS
        if context is None:
            context = {}

        super().__init__(
            prompt=prompt,
            commands=commands,
            client_session=client_session,
            context=context,
        )

    async def _initialize_autocomplete(self) -> None:
        all_agent_templates = await self.environment[
            "rest_api"
        ].get_all_agent_templates()
        all_agent_generators = await self.environment[
            "rest_api"
        ].get_all_agent_generators()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        for key, value in {
            command: {
                agent_generator["agent_generator_id"]: None
                for agent_generator in all_agent_generators
            }
            for command in [
                "cancel_generator",
                "delete_generator",
                "info_generator",
                "redescribe_generator",
                "rename_generator",
                "start_generator",
                "stop_generator",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                agent_template["agent_template_id"]: None
                for agent_template in all_agent_templates
            }
            for command in [
                "info_agent_template",
                "use_agent_template",
            ]
        }.items():
            nested_completer_dict[key] = value
        for key, value in {
            command: {
                agent_generator["agent_generator_id"]: dict.fromkeys(
                    agent_generator["parameters"]
                )
                for agent_generator in all_agent_generators
            }
            for command in [
                "set_generator_parameter",
                "unset_generator_parameter",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    # We don't actually care about the event content so we just ignore it. We just need to
    # know a change happened so that we can update the autocompleter.
    async def _agent_generator_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        await self._initialize_autocomplete()

    async def _setup_event_handlers(self) -> None:
        await self.environment["websockets_api"].subscribe_to_event(
            event_type="AGENT_GENERATOR_CREATED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.environment["websockets_api"].subscribe_to_event(
            event_type="AGENT_GENERATOR_REMOVED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.environment["websockets_api"].start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.environment["websockets_api"].stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.environment["websockets_api"].unsubscribe_from_event(
            event_type="AGENT_GENERATOR_CREATED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.environment["websockets_api"].unsubscribe_from_event(
            event_type="AGENT_GENERATOR_REMOVED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )

    async def on_enter(self) -> None:
        await self._initialize_autocomplete()
        await self._setup_event_handlers()

    async def on_exit(self) -> None:
        # The exit command when executed will disconnect the websocket connection but
        # this method will still run so we need to first check if the client websockets
        # API connection has already been disconnected.
        if self.environment["websockets_api"].connected:
            await self._teardown_event_handlers()
