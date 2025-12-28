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
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_snake_case_to_title,
)
from consortium.client.utils.printer_utils import console, print_error


class InfoAgentTemplateOptionsCommand(BaseCommand):
    name = "info_agent_template_option"
    description = "Display detailed information about a specific agent template option."
    epilog = format_argparse_epilog(
        """
        Examples:
          info_agent_template_option remote_host
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_option_name",
            help=(
                "The name of the agent template option to display detailed information "
                "for."
            ),
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            agent_template = context.interpreter_context["agent_template"]
            try:
                option = agent_template["options"][
                    parsed_args.agent_template_option_name[0]
                ]
            except KeyError:
                print_error(
                    f"Agent template option with name "
                    f"{parsed_args.agent_template_option_name[0]} not found.",
                )
                return ReturnStatus(
                    type=ReturnStatusType.CONTINUE,
                )

            table = Table(title="Agent Template Option Information")
            table.add_column("Information")
            table.add_column("Data")
            for key, value in option.items():
                table.add_row(format_snake_case_to_title(key), str(value))

            console.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
