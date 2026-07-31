from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_snake_case_to_title,
)
from consortium.client.utils.printer_utils import console, print_error


class ListenerTemplateOptionCommand(BaseConnectedCommand):
    name = "option"
    description = (
        "Manage the current listener template's options through its sub-commands"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          option list
          option info local_host

        Notes:
          Every sub-command carries its own help, for example:
            option info --help
        """,
    )
    group = "Listener Template Management Commands"
    autocompletes = {
        "list": None,
        "info": Autocomplete.TEMPLATE_OPTION,
    }

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help=(
                "List all options for the current listener template along with their "
                "essential information."
            ),
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  option list
                """,
            ),
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help=(
                "Display information about a specific listener template option by its "
                "name."
            ),
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  option info local_host
                """,
            ),
        )
        parser_info.add_argument(
            "option_name",
            help="Name of the listener template option to display information for.",
            nargs=1,
        )

    @staticmethod
    def _handle_list_sub_command(
        context: ConnectedContext,
    ) -> InterpreterSignal:
        listener_template_options = context.interpreter_context.listener_template[
            "options"
        ]

        table = Table(title="Listener Template Options", highlight=True)
        table.add_column("Name")
        table.add_column("Option Type")
        table.add_column("Description")
        table.add_column("Required")
        table.add_column("Current Value")
        for option_name, option in sorted(listener_template_options.items()):
            table.add_row(
                option_name,
                option["option_type"],
                option["description"],
                str(option["required"]),
                str(option["value"]) if option["value"] is not None else "",
            )
        console.print(table, "")

        return ContinueSignal()

    @staticmethod
    def _handle_info_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        listener_template = context.interpreter_context.listener_template

        try:
            option = listener_template["options"][parsed_args.option_name[0]]
        except KeyError:
            print_error(
                f"Listener template option not found: '{parsed_args.option_name[0]}'",
            )
            return ContinueSignal()

        table = Table(
            title="Listener Template Option Information",
            highlight=True,
            show_footer=True,
        )
        table.add_column("Information", footer="[bold yellow]Current Value[/]")
        table.add_column(
            "Data",
            footer=str(option["value"]) if option["value"] is not None else "",
        )
        for key, value in option.items():
            if key != "value":
                table.add_row(format_snake_case_to_title(key), str(value))
        console.print(table, "")

        return ContinueSignal()

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "list":
                    return self._handle_list_sub_command(context=context)
                case "info":
                    return self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown option sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
