from rich.table import Table

from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import console


class AgentTemplateListOptionCommand(BaseCommand):
    name = "opt-list"
    description = (
        "List all options for the current agent template along with their "
        "essential information"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          opt-list
        """,
    )
    group = "Agent Template Management Commands"

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            agent_template_options = context.interpreter_context["agent_template"][
                "options"
            ]

            table = Table(title="Agent Template Options", highlight=True)
            table.add_column("Option Type")
            table.add_column("Name")
            table.add_column("Description")
            table.add_column("Required")
            table.add_column("Current Value")
            for option_name, option in sorted(agent_template_options.items()):
                table.add_row(
                    option["option_type"],
                    option_name,
                    option["description"],
                    str(option["required"]),
                    str(option["value"]) if option["value"] is not None else "",
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
