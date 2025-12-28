from argparse import ArgumentParser

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
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
          unset_agent_template_option option_str
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_str",
            help="Name of the agent template option to unset the value of.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            agent_template_options = context.interpreter_context["agent_template"][
                "options"
            ]
            option_name = parsed_args.option_name[0]

            try:
                option = agent_template_options[option_name]
            except KeyError:
                print_error(
                    f"Option '{option_name}' does not exist in the agent template.",
                )
                return ReturnStatus(ReturnStatusType.CONTINUE)

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

        return ReturnStatus(ReturnStatusType.CONTINUE)
