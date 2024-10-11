from argparse import ArgumentParser

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success


class UnsetAgentTemplateOptionCommand(BaseCommand):
    name = "unset_agent_template_option"
    description = (
        "Unset an agent template option for the currently selected agent template "
        "being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          unset_agent_template_option option_name
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the agent template option to unset the value of.",
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

            if option["option_type"] == "LIST_VALUE_OPTION":
                option["value"] = []
                print_success(
                    f'Option "{option_name}" has been unset.',
                )
            elif option["option_type"] == "DICTIONARY_VALUE_OPTION":
                option["value"] = {}
                print_success(
                    f'Option "{option_name}" has been unset.',
                )
            elif option["option_type"] == "TOGGLEABLE_CHOICES_VALUE_OPTION":
                print_error(
                    f'Option "{option_name}" is of option type '
                    f'"{option["option_type"]}" and cannot be unset.',
                )
            # SINGLE_VALUE_OPTION and CHOICE_VALUE_OPTION
            else:
                option["value"] = None
                print_success(
                    f'Option "{option_name}" has been unset.',
                )
        except SystemExit:
            pass

        return ReturnStatus(ClientReturnStatusType.CONTINUE)
