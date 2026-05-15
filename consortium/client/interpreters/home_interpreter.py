from collections import deque
from typing import TYPE_CHECKING

from prompt_toolkit import ANSI
from prompt_toolkit.completion import NestedCompleter

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.home_interpreter_commands import (
    HOME_INTERPRETER_COMMANDS,
)
from consortium.client.models.alias_model import Alias
from consortium.client.repl_interface.base_interpreter import BaseInterpreter
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

client_sessions_service = client_singletons.client_sessions_service


class HomeInterpreter(BaseInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        aliases: dict[str, Alias],
        resource_commands: deque[str],
    ):
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium (Home)\n> ")),
            commands=[
                command
                for command in HOME_INTERPRETER_COMMANDS
                if command.name != "home"
            ]
            + CORE_COMMANDS,
            client_session=client_session,
            aliases=aliases,
            resource_commands=resource_commands,
        )

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
    async def on_loop(self) -> None:
        all_client_sessions = client_sessions_service.get_all_client_sessions()

        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            completer=self.prompt_session.completer,
        )
        for key, value in {
            command: {
                str(client_session.client_session_id): None
                for client_session in all_client_sessions
            }
            for command in [
                "disconnect",
                "info",
                "interact",
                "rename",
                "describe",
            ]
        }.items():
            nested_completer_dict[key] = value
        nested_completer_dict["help"] = dict.fromkeys(self.commands)

        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )
