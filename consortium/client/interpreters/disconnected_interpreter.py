from prompt_toolkit import ANSI

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.disconnected_interpreter_commands import (
    DISCONNECTED_INTERPRETER_COMMANDS,
)
from consortium.client.commands.home_interpreter_commands import (
    ClientSessionListCommand,
    ConnectCommand,
    InteractClientSessionCommand,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.base_interpreter import (
    BaseDisconnectedInterpreter,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

client_sessions_service = client_singletons.client_sessions_service


class DisconnectedInterpreter(BaseDisconnectedInterpreter):
    def __init__(
        self,
        interpreter_context: BaseInterpreterContext,
    ):
        combined_disconnected_interpreter_core_commands = (
            [
                command
                for command in CORE_COMMANDS
                if command.name not in ("home", "listeners", "generators", "agents")
            ]
            + DISCONNECTED_INTERPRETER_COMMANDS
            + [
                ConnectCommand(),
                ClientSessionListCommand(),
                InteractClientSessionCommand(),
            ]
        )
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium\n> ")),
            commands=[
                *combined_disconnected_interpreter_core_commands,
            ],
            client_session=None,
            interpreter_context=interpreter_context,
        )

    async def on_enter(self) -> None:
        all_client_sessions = client_sessions_service.get_all_client_sessions()
        ClientSessionListCommand._list_all_client_sessions(
            all_client_sessions=all_client_sessions
        )

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
