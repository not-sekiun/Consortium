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


class InfoListenerTemplateCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all info for a specific listener template.",
            prog="info_listener_template",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    info_listener_template 123e4567-e89b-12d3-a456-42661417400  # Display info for the listener template with listener template ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener template to display info for.",
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

            listener_template = (
                await client_session.get_listener_template_by_listener_template_id(
                    parsed_args.listener_template_id[0],
                )
            )

            table = Table(title="Listener Template Info")
            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Listener Template ID",
                listener_template["listener_template_id"],
            )
            table.add_row("Listener Name", listener_template["name"])
            table.add_row("Listener Description", listener_template["description"])
            table.add_row(
                "Listener Type ID",
                listener_template["listener_type"]["listener_type_id"],
            )
            table.add_row(
                "Listener Type Name",
                listener_template["listener_type"]["name"],
            )
            table.add_row(
                "Listener Type Description",
                listener_template["listener_type"]["description"],
            )
            table.add_row("Authors", str(listener_template["authors"]))

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
