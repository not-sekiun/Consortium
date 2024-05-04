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
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE


class InfoAgentTemplateCommand(BaseCommand):
    name = "info_agent_template"
    description = (
        "Show all information for a specific agent template or for the currently used "
        "agent template."
    )
    epilog = format_argparse_epilog(
        """
        Example:
            info_agent_template 123e4567-e89b-12d3-a456-42661417400  # Display information for the agent template with agent template ID 123e4567-e89b-12d3-a456-42661417400
            info_agent_template  # Running the command without a specified agent template ID will show information for the currently used agent template
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="Agent template ID of the agent template to display information for.",
            nargs="?",
            default=None,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            if parsed_args.agent_template_id is None:
                agent_template = command_context.environment["agent_template"]
            else:
                agent_template = await command_context.environment[
                    "client_connection"
                ].get_agent_template_by_agent_template_id(
                    parsed_args.agent_template_id,
                )

            table = Table(title="Agent Template Info")

            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Agent Template ID",
                agent_template["agent_template_id"],
            )
            table.add_row("Name", agent_template["name"])
            table.add_row("Description", agent_template["description"])
            agent_type_table = Table()
            agent_type_table.add_column("Information")
            agent_type_table.add_column("Data")
            agent_type_table.add_row(
                "Agent Type ID",
                agent_template["agent_type"]["agent_type_id"],
            )
            agent_type_table.add_row(
                "Name",
                agent_template["agent_type"]["name"],
            )
            agent_type_table.add_row(
                "Compatible Listener Types",
                "\n".join(
                    [
                        listener_type["name"]
                        + " ("
                        + listener_type["listener_type_id"]
                        + ")"
                        for listener_type in agent_template["agent_type"][
                            "compatible_listener_types"
                        ]
                    ],
                ),
            )
            table.add_row(
                "Agent Type",
                agent_type_table,
            )
            table.add_row("Authors", "\n".join(agent_template["authors"]))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
