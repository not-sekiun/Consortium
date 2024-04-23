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
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class InfoListenerTemplateCommand(BaseCommand):
    name = "info_listener_template"
    description = "Show all information for a specific listener template."
    epilog = argparse_epilog_formatter(
        """
        Example:
            info_listener_template 123e4567-e89b-12d3-a456-42661417400  # Display information for the listener template with listener template ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener template to display information for.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            listener_template = await command_context.environment[
                "client_connection"
            ].get_listener_template_by_listener_template_id(
                parsed_args.listener_template_id[0],
            )

            table = Table(title="Listener Template Info")

            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Listener Template ID",
                listener_template["listener_template_id"],
            )
            table.add_row("Name", listener_template["name"])
            table.add_row("Description", listener_template["description"])
            listener_type_table = Table()
            listener_type_table.add_column("Information")
            listener_type_table.add_column("Data")
            listener_type_table.add_row(
                "Listener Type ID",
                listener_template["listener_type"]["listener_type_id"],
            )
            listener_type_table.add_row(
                "Name",
                listener_template["listener_type"]["name"],
            )
            listener_type_table.add_row(
                "Compatible Agent Type IDs",
                "\n".join(
                    listener_template["listener_type"]["compatible_agent_type_ids"],
                ),
            )
            table.add_row(
                "Listener Type",
                listener_type_table,
            )
            table.add_row("Authors", str(listener_template["authors"]))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
