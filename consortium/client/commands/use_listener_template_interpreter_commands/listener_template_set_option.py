from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_value_type_specification_epilog,
    format_value_type_specification_with_examples_epilog,
)
from consortium.client.utils.options_utils import (
    convert_option_value_strings_to_option_value,
)
from consortium.client.utils.printer_utils import (
    print_error,
    print_success,
)


class ListenerTemplateSetOptionCommand(BaseCommand):
    name = "set"
    description = "Set the current listener template's option to a specific value"
    epilog = format_value_type_specification_epilog()
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the listener template option to set the value of.",
            nargs=1,
        )
        parser.add_argument(
            "option_values",
            help="Value to set listener template option to.",
            nargs="+",
        )
        parser.add_argument(
            "--value-type",
            "-t",
            help="Value type to use for a listener template option. Applies to all values.",
            choices={"str", "int", "float", "bool"},
            nargs="?",
            default=None,
            metavar="VALUE_TYPE",
        )
        parser.add_argument(
            "--help-full",
            help="Show full help message with examples.",
            action="store_true",
            default=False,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            if "--help-full" in context.arguments:
                self.parser.epilog = (
                    format_value_type_specification_with_examples_epilog(
                        example_prefix="set <option_name>"
                    )
                )
                self.parser.print_help()
                self.parser.epilog = self.epilog
                return ContinueSignal()

            parsed_args = self.parser.parse_args(context.arguments)
            listener_template_options = context.interpreter_context[
                "listener_template"
            ]["options"]

            option_name = parsed_args.option_name[0]
            option_values = parsed_args.option_values
            value_type = parsed_args.value_type

            try:
                option = listener_template_options[option_name]
            except KeyError:
                print_error(
                    f"Listener template option not found: '{option_name}'",
                )
                return ContinueSignal()

            try:
                option_name, option_value = (
                    convert_option_value_strings_to_option_value(
                        option_json_data=option,
                        value_strings=option_values,
                        value_type_flag=value_type,
                    )
                )
                option["value"] = option_value
                print_success(
                    f"Set listener template option '{option_name}' to '{option_value}'",
                )
            except ValueError as exc:
                print_error(exc)
                return ContinueSignal()
        except SystemExit:
            pass

        return ContinueSignal()
