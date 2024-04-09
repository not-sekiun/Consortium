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


class ListClientSessionsCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all current client sessions.",
            prog="list_client_sessions",
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
            all_client_sessions = client_sessions_service.get_all_client_sessions()
            table = Table(title="Client Sessions")
            table.add_column("Client Session ID")
            table.add_column("Name")

            for client_session in all_client_sessions:
                table.add_row(
                    str(client_session.client_session_id),
                    client_session.name,
                )

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
