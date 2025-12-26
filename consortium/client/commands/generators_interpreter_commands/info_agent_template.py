from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE


class InfoAgentTemplateCommand(BaseCommand):
    name = "info_agent_template"
    description = "Display detailed information about a specific agent template"
    epilog = format_argparse_epilog(
        """
        Examples:
          info_agent_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help=(
                "Agent template ID of the agent template to display detailed "
                "information for."
            ),
            nargs=1,
        )

    def _display_agent_template_info(self, agent_template: dict) -> None:
        table = Table(title="Agent Template Information")
        table.add_column("Information")
        table.add_column("Data")
        table.add_row(
            "Agent Template ID",
            agent_template["agent_template_id"],
        )
        table.add_row(
            "Label",
            agent_template["label"],
        )
        table.add_row("Name", agent_template["name"])
        table.add_row("Description", agent_template["description"])
        table.add_row("Version", agent_template["version"])
        table.add_row(
            "Compatible Framework Version",
            agent_template["compatible_framework_version"],
        )
        table.add_row("Authors", "\n".join(agent_template["authors"]))
        table.add_row(
            "Agent Type",
            agent_template["agent_type"]["name"],
        )
        table.add_row(
            "Compatible Listener Types",
            "\n".join(
                list(agent_template["compatible_listener_types"]),
            ),
        )
        CONSOLE.print(table)

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.environment["rest_api"]
            agent_template = await client_rest_api_connection.get_agent_template_by_agent_template_id(
                parsed_args.agent_template_id[0],
            )
            self._display_agent_template_info(agent_template=agent_template)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
