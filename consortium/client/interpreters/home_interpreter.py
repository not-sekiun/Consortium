from typing import TYPE_CHECKING

from prompt_toolkit import ANSI

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.home_interpreter_commands import (
    HOME_INTERPRETER_COMMANDS,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

client_sessions_service = client_singletons.client_sessions_service


class HomeInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
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
            interpreter_context=interpreter_context,
        )

    # TODO: Find a way for interpreters to "inherit" command completions or share
    #  common command completions. Probably could just make it a parameter
    async def on_loop(self) -> None:
        all_client_sessions = client_sessions_service.get_all_client_sessions()

        completions_dict = self.completer.get_completions_dict()

        client_session_ids_completion = {
            str(client_session.client_session_id): None
            for client_session in all_client_sessions
        }
        for command in ["disconnect", "info", "interact", "rename", "describe"]:
            completions_dict[command] = client_session_ids_completion

        completions_dict["help"] = dict.fromkeys(self.commands)

        self.completer.set_completions_dict(completions_dict)
