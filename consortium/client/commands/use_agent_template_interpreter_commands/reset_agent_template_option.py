import copy
from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success


class ResetAgentTemplateOptionCommand(BaseCommand):
    name = "reset_agent_template_option"
    description = (
        "Reset an agent template option to its default value for the currently "
        "selected agent template being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            reset_agent_template_option option_name
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the agent template option to reset the value of.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            agent_template_options = command_context.environment["agent_template"][
                "options"
            ]
            option_name = parsed_args.option_name[0]

            try:
                option = agent_template_options[option_name]
            except KeyError:
                print_error(
                    f"Option '{option_name}' does not exist in the agent template.",
                )
                return ReturnStatus(ClientReturnStatusType.CONTINUE)

            option["value"] = copy.deepcopy(option["default_value"])
            print_success(
                f'Option "{option_name}" has been reset to its default value '
                f'"{option["value"]}".',
            )
        except SystemExit:
            pass

        return ReturnStatus(ClientReturnStatusType.CONTINUE)
