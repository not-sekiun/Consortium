from argparse import ArgumentParser

from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import CONSOLE


class InfoListenerCommand(BaseCommand):
    name = "info_listener"
    description = "Display detailed information about a specific listener."
    epilog = format_argparse_epilog(
        """
        Examples:
            info_listener 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="The listener ID of the listener to display detailed information for.",
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
                "\n".join(
                    [
                        agent_type["name"] + " (" + agent_type["agent_type_id"] + ")"
                        for agent_type in listener["listener_type"][
                            "compatible_agent_types"
                        ]
                    ],
                ),
            )
            table.add_row("Listener Type", listener_type_table)
            parameter_table = Table()
            parameter_table.add_column("Parameter")
            parameter_table.add_column("Value")
            for parameter_name, parameter_value in listener["parameters"].items():
                parameter_table.add_row(parameter_name, str(parameter_value))
            table.add_row("Parameters", parameter_table)
            table.add_row(
                "Status",
                format_listener_state_string_with_color(listener["status"]["state"]),
            )
            table.add_row("Datetime Created", listener["datetime_created"])
            table.add_row("Connected Agents IDs", "\n".join(listener["agent_ids"]))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
