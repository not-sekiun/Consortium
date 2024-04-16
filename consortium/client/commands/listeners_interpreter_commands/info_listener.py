from argparse import ArgumentParser

from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class InfoListenerCommand(BaseCommand):
    name = "info_listener"
    description = "List all information for a specific listener."
    epilog = argparse_epilog_formatter(
        """
        Example:
            info_listener 123e4567-e89b-12d3-a456-42661417400  # Display information for the listener with listener ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to display information for.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            listener = await command_context.environment[
                "client_connection"
            ].get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )

            table = Table(title="Listener Information")

            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Listener ID",
                listener["listener_id"],
            )
            table.add_row("Listener Name", listener["name"])
            table.add_row("Listener Description", listener["description"])
            table.add_row(
                "Listener Type ID",
                listener["listener_type"]["listener_type_id"],
            )
            table.add_row("Authors", str(listener["authors"]))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
