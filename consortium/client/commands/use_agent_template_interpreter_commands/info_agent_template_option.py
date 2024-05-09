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
    format_snake_case_to_title,
)
from consortium.client.utils.printer_utils import CONSOLE, print_error


class InfoAgentTemplateOptionsCommand(BaseCommand):
    name = "info_agent_template_option"
    description = "Display detailed information about a specific agent template option."
    epilog = format_argparse_epilog(
        """
        Examples:
            info_agent_template_option remote_host
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_option_name",
            help=(
                "The name of the agent template option to display detailed information "
                "for."
            ),
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            agent_template = command_context.environment["agent_template"]
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
                    type=ClientReturnStatusType.CONTINUE,
                )

            table = Table(title="Agent Template Option Information")
            table.add_column("Information")
            table.add_column("Data")
            for key, value in option.items():
                table.add_row(format_snake_case_to_title(key), str(value))

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
