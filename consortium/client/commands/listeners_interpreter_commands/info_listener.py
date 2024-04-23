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


class InfoListenerCommand(BaseCommand):
    name = "info_listener"
    description = "Show all information for a specific listener."
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

            client_connection = command_context.environment["client_connection"]

            listener = await client_connection.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )
            CONSOLE.print(listener)

            table = Table(title="Listener Information")
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Listener ID",
                listener["listener_id"],
            )
            table.add_row("Name", listener["name"])
            table.add_row("Description", listener["description"])
            table.add_row("Endpoint", listener["endpoint"])
            listener_type_table = Table()
            listener_type_table.add_column("Information")
            listener_type_table.add_column("Data")
            listener_type_table.add_row(
                "Listener Type ID",
                listener["listener_type"]["listener_type_id"],
            )
            listener_type_table.add_row(
                "Name",
                listener["listener_type"]["name"],
            )
            listener_type_table.add_row(
                "Compatible Agent Types",
                "\n".join(listener["listener_type"]["compatible_agent_type_ids"]),
            )
            table.add_row("Listener Type", listener_type_table)
            options_table = Table()
            options_table.add_column("Option")
            options_table.add_column("Value")
            for option_name, option in listener["options"].items():
                options_table.add_row(option_name, str(option["value"]))
            table.add_row("Options", options_table)
            table.add_row("Status", str(listener["status"]["state"]))
            table.add_row("Datetime Created", listener["datetime_created"])
            table.add_row("Agent IDs", "\n".join(listener["agent_ids"]))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
