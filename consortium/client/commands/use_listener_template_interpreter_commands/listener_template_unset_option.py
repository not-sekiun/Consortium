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
from consortium.client.utils.options_utils import OptionType
from consortium.client.utils.printer_utils import print_error, print_success


class ListenerTemplateUnsetOptionCommand(BaseCommand):
    name = "unset"
    description = "Unset the current listener template's option to an empty value"
    epilog = format_argparse_epilog(
        """
        Examples:
          unset option_name
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the agent template option to unset the value of.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            listener_template_options = context.interpreter_context[
                "listener_template"
            ]["options"]
            option_name = parsed_args.option_name[0]

            try:
                option = listener_template_options[option_name]
            except KeyError:
                print_error(
                    f"Listener template option not found: '{option_name}'",
                )
                return ReturnStatus(ReturnStatusType.CONTINUE)

            if option["option_type"] == OptionType.LIST_VALUE_OPTION:
                option["value"] = []
                print_success(
                    f"Unset listener template option: '{option_name}'",
                )
            elif option["option_type"] == OptionType.DICTIONARY_VALUE_OPTION:
                option["value"] = {}
                print_success(
                    f"Unset listener template option: '{option_name}'",
                )
            elif option["option_type"] == OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION:
                print_error(
                    f"Listener template option '{option_name}' is of option type "
                    f"'{option['option_type']}' which cannot be unset",
                )
            elif option["option_type"] in (
                OptionType.SINGLE_VALUE_OPTION,
                OptionType.CHOICE_VALUE_OPTION,
            ):
                option["value"] = None
                print_success(
                    f"Unset listener template option: '{option_name}'",
                )
            else:
                raise AssertionError(
                    f"Unhandled option type '{option['option_type']}' "
                    f"for listener template option unset",
                )
        except SystemExit:
            pass

        return ReturnStatus(ReturnStatusType.CONTINUE)
