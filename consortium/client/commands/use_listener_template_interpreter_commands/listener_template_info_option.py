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
from consortium.client.utils.printer_utils import console, print_error


class ListenerTemplateInfoOptionCommand(BaseCommand):
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
            "option_name",
            help="Name of the listener template option to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            listener_template = context.interpreter_context["listener_template"]

            try:
                option = listener_template["options"][parsed_args.option_name[0]]
            except KeyError:
                print_error(
                    f"Listener template option not found: "
                    f"'{parsed_args.option_name[0]}'",
                )
                return ReturnStatus(
                    type=ReturnStatusType.CONTINUE,
                )
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
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
