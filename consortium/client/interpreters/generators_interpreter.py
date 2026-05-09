from collections import deque
from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI, HTML
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.generators_interpreter_commands import (
    GENERATORS_INTERPRETER_COMMANDS,
    AgentTemplateListCommand,
    GeneratorListCommand,
)
from consortium.client.models.alias_model import Alias
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.repl_interface.base_interpreter import BaseInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS = [
    command for command in CORE_COMMANDS if command.name != "generators"
] + GENERATORS_INTERPRETER_COMMANDS


class GeneratorsInterpreter(BaseInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        aliases: dict[str, Alias],
        resource_commands: deque[str],
        prompt: str | ANSI | HTML | list[tuple[str, str]] | None = None,
        commands: list[BaseCommand] | None = None,
        interpreter_context: dict[str, Any] | None = None,
    ):
        if prompt is None:
            prompt = HTML(
                "<b>Consortium (<ansigreen>Generators</ansigreen>)\n> </b>",
            )
        if commands is None:
            commands = COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS
        if interpreter_context is None:
            interpreter_context = {}

        super().__init__(
            prompt=prompt,
            commands=commands,
            client_session=client_session,
            aliases=aliases,
            resource_commands=resource_commands,
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

    async def _initialize_autocomplete(
        self,
        all_agent_generators: list[dict[str, Any]],
        all_agent_templates: list[dict[str, Any]],
    ) -> None:
        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )

        # Register commands that take the agent generator ID as the first positional
        # argument to autocomplete with.
        for key, value in {
            command: {
                agent_generator["agent_generator_id"]: None
                for agent_generator in all_agent_generators
            }
            for command in [
                "start",
                "stop",
                "cancel",
                "delete",
                "info",
                "rename",
                "describe",
            ]
        }.items():
            nested_completer_dict[key] = value

        # Register the "update" command to autocomplete with the agent generator ID as
        # the first positional argument and the parameters of the agent generator as
        # the second positional argument.
        nested_completer_dict["update"] = {
            agent_generator["agent_generator_id"]: dict.fromkeys(
                agent_generator["parameters"]
            )
            for agent_generator in all_agent_generators
        }

        # Register commands that take the agent template ID as the first positional
        # argument to autocomplete with.
        for key, value in {
            command: {
                agent_template["agent_template_id"]: None
                for agent_template in all_agent_templates
            }
            for command in [
                "at-info",
                "use",
            ]
        }.items():
            nested_completer_dict[key] = value

        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

    async def _agent_generator_created_or_removed_event_handler(
        self,
        _event: dict[str, Any],
    ) -> None:
        (
            all_agent_generators,
            all_agent_templates,
        ) = await self._get_all_agent_generators_and_agent_templates()
        await self._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
        )

    async def _setup_event_handlers(self) -> None:
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_GENERATOR_CREATED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.client_session.websockets_api.subscribe_to_event(
            event_type="AGENT_GENERATOR_REMOVED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.client_session.websockets_api.start()

    async def _teardown_event_handlers(self) -> None:
        # Stop the message consumption loop for the websocket connection just so that
        # the action message being sent next doesn't need to go through the message
        # consumer handler loop. This is not necessary but just makes it cleaner.
        await self.client_session.websockets_api.stop()
        # Remove all relevant event handlers to prevent them from firing in other
        # interpreters.
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_GENERATOR_CREATED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
        )
        await self.client_session.websockets_api.unsubscribe_from_event(
            event_type="AGENT_GENERATOR_REMOVED",
            event_handler=self._agent_generator_created_or_removed_event_handler,
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
        await self._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
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
