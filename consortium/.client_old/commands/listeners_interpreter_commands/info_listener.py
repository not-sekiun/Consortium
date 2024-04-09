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

client_sessions_service = client_singletons.client_sessions_service


class InfoListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all info for a specific listener.",
            prog="info_listener",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    info_listener 123e4567-e89b-12d3-a456-42661417400  # Display info for the listener with listener ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to display info for.",
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

            listener = await client_session.get_listener_by_listener_id(
                parsed_args.listener_template_id[0],
            )
            print(listener)

            table = Table(title="Listener Info")
            table.add_column("Information")
            table.add_column("Data")

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
