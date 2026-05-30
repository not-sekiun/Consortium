from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_snake_case_to_title,
)
from consortium.client.utils.printer_utils import console, print_error


class AgentTemplateInfoOptionCommand(BaseCommand[ConnectedContext]):
    name = "opt-info"
    description = (
        "Display information about a specific agent template option by its name"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          opt-info remote_host
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the agent template option to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            agent_template = context.interpreter_context.agent_template

            try:
                option = agent_template["options"][parsed_args.option_name[0]]
            except KeyError:
                print_error(
                    f"Agent template option not found: '{parsed_args.option_name[0]}'",
                )
                return ContinueSignal()

            table = Table(
                title="Agent Template Option Information",
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

        return ContinueSignal()
