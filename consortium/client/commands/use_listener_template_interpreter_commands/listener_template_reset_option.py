import copy
from argparse import ArgumentParser

from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success


class ListenerTemplateResetOptionCommand(BaseCommand):
    name = "reset"
    description = "Reset the current listener template's option to its default value"
    epilog = format_argparse_epilog(
        """
        Examples:
          reset option_name
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the listener template option to reset.",
            nargs=1,
        )

    async def run(self, context: Context) -> InterpreterSignal:
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
                return ContinueSignal()

            option["value"] = copy.deepcopy(option["default_value"])
            print_success(
                f"Reset listener template option '{option_name}' to its default value '{option['value']}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
