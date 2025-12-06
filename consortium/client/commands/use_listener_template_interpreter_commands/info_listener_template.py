from argparse import ArgumentParser

from rich.table import Table

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE


class InfoListenerTemplateCommand(BaseCommand):
    name = "info_listener_template"
    description = (
        "Display detailed information about a specific listener template or for the "
        "currently selected listener template being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info_listener_template  # Displays detailed information for the currently selected listener template being used if the listener template ID is not specified.
          info_listener_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help=(
                "The listener template ID of the listener template to display detailed "
                "information for. If not provided, detailed information for the "
                "currently selected listener template is displayed."
            ),
            nargs="?",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            if parsed_args.listener_template_id is None:
                listener_template = command_context.environment["listener_template"]
            else:
                listener_template = await client_rest_api_connection.get_listener_template_by_listener_template_id(
                    parsed_args.listener_template_id,
                )

            table = Table(title="Listener Template Information")
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Listener Template ID",
                listener_template["listener_template_id"],
            )
            table.add_row(
                "Label",
                listener_template["label"],
            )
            table.add_row("Name", listener_template["name"])
            table.add_row("Description", listener_template["description"])
            table.add_row("Version", listener_template["version"])
            table.add_row(
                "Compatible Framework Version",
                listener_template["compatible_framework_version"],
            )
            table.add_row("Authors", "\n".join(listener_template["authors"]))
            table.add_row(
                "Listener Type",
                f"{listener_template["listener_type"]["name"]} ({listener_template["listener_type"]["listener_type_id"]})",
            )
            table.add_row(
                "Compatible Agent Types",
                "\n".join(
                    [
                        f"{agent_type["name"]} ({agent_type["agent_type_id"]})"
                        for agent_type in listener_template["listener_type"][
                            "compatible_agent_types"
                        ]
                    ],
                ),
            )
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
