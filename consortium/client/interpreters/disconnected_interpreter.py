from prompt_toolkit import ANSI

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.commands.disconnected_interpreter_commands import (
    SESSION_COMMAND,
    SessionCommand,
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
        # The core session command is replaced with the disconnected variant rather than
        # omitted outright: there is no current client session to fall back on here, so
        # its sub-commands take the client session ID they operate on.
        combined_disconnected_interpreter_core_commands = [
            command
            for command in CORE_COMMANDS
            if command.name
            not in ("home", "listeners", "generators", "agents", SESSION_COMMAND.name)
        ] + [SESSION_COMMAND]
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium\n> ")),
            commands=combined_disconnected_interpreter_core_commands,
            client_session=None,
            interpreter_context=interpreter_context,
        )

    async def on_enter(self) -> None:
        all_client_sessions = client_sessions_service.get_all_client_sessions()
        SessionCommand._list_all_client_sessions(
            all_client_sessions=all_client_sessions
        )
