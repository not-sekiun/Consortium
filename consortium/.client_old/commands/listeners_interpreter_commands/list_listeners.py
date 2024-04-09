import argparse

from rich.console import Console
from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)

client_sessions_service = client_singletons.client_sessions_service


class ListListenersCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all listeners.",
            prog="list_listeners",
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            all_listeners = await client_session.get_all_listeners()

            table = Table(title="Listeners")
            table.add_column("Listener ID")
            table.add_column("Name")

            for listener in all_listeners:
                table.add_row(
                    listener["listener_id"],
                    listener["name"],
                )

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
