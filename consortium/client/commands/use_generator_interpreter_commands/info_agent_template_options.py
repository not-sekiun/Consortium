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
from consortium.client.utils.printer_utils import CONSOLE, print_error
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class InfoAgentTemplateOptionsCommand(BaseCommand):
    name = "info_agent_template_options"
    description = "Show all information for a specific agent template option."
    epilog = argparse_epilog_formatter(
        """
        Example:
            info_options_agent_template remote_host # Display information for the agent template option with name remote_host
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_option_name",
            help="Agent template option name of the agent template option to display information for.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            table = Table(title="Agent Template Option Information")
            table.add_column("Information")
            table.add_column("Data")

            try:
                option = command_context.environment["agent_template"]["options"][
                    parsed_args.agent_template_option_name[0]
                ]
            except KeyError:
                print_error(
                    f"Agent template option with name {parsed_args.agent_template_option_name[0]} not found.",
                )
                return ReturnStatus(
                    type=ClientReturnStatusType.CONTINUE,
                )

            for key, value in option.items():
                table.add_row(
                    key,
                    str(value),
                )

            CONSOLE.print(
                table,
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
