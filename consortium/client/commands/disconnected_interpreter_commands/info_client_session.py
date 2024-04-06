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
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error

client_connections_service = client_singletons.client_sessions_service


class InfoClientSessionCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all info for a specific client session.",
            prog="info_client_session",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    info_client_session 123e4567-e89b-12d3-a456-42661417400  # Display info for the client session with client session ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "client_session_id",
            help="Client session ID of the client session to display info for. If not passed in, info for the current client session is displayed",
            nargs=1,
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

            try:
                target_client_session = (
                    client_connections_service.get_client_session_by_client_session_id(
                        parsed_args.client_session_id[0],
                    )
                )
            except ValueError as exc:
                print_error(str(exc))
                return ContinueReturnStatus()

            table = Table(title="Client Session Info")
            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Client Session ID",
                str(target_client_session.client_session_id),
            )
            table.add_row("Name", target_client_session.name)
            table.add_row("Username", target_client_session.client_config.username)
            table.add_row("Password", target_client_session.client_config.password)
            table.add_row(
                "Remote Host",
                target_client_session.client_config.remote_host,
            )
            table.add_row(
                "Remote Port",
                str(target_client_session.client_config.remote_port),
            )
            table.add_row(
                "Datetime Connected",
                str(target_client_session.datetime_connected.isoformat()),
            )

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
