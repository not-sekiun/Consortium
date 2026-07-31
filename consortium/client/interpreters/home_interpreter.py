from typing import TYPE_CHECKING

from prompt_toolkit import ANSI

from consortium.client.commands.core_commands import CORE_COMMANDS
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.repl_interface.base_interpreter import (
    BaseConnectedInterpreter,
)
from consortium.client.utils.formatter_utils import format_rich_text_as_ansi

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class HomeInterpreter(BaseConnectedInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: BaseInterpreterContext,
    ):
        # The session command this interpreter used to own is a core command now, so the
        # home interpreter is left with nothing but the core commands.
        super().__init__(
            prompt=ANSI(format_rich_text_as_ansi("[bold white]Consortium (Home)\n> ")),
            commands=CORE_COMMANDS,
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def on_enter(self) -> None:
        await self.client_session.websockets_api.start()

    async def on_exit(self) -> None:
        await self.client_session.websockets_api.stop()
