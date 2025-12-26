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
from consortium.client.utils.printer_utils import CONSOLE, print_error


class InfoListenerTemplateOptionsCommand(BaseCommand):
    name = "opt-info"
    description = (
        "Display information about a specific listener template option by its name"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          opt-info local_host
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_option_name",
            help=("Name of the listener template option to display information for."),
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            listener_template = context.environment["listener_template"]

            try:
                option = listener_template["options"][
                    parsed_args.listener_template_option_name[0]
                ]
            except KeyError:
                print_error(
                    f"Listener template option with name "
                    f"{parsed_args.listener_template_option_name[0]} not found.",
                )
                return ReturnStatus(
                    type=ReturnStatusType.CONTINUE,
                )
            table = Table(title="Listener Template Option Information", highlight=True)
            table.add_column("Information")
            table.add_column("Data")
            for key, value in option.items():
                table.add_row(format_snake_case_to_title(key), str(value))
            CONSOLE.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
