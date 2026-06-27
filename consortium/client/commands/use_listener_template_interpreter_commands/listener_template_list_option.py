from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import console


class ListenerTemplateListOptionCommand(BaseConnectedCommand):
    name = "opt-list"
    description = (
        "List all options for the current listener template along with their "
        "essential information"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          opt-list
        """,
    )
    group = "Listener Template Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
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

            console.print(table)
        except SystemExit:
            pass

        return ContinueSignal()
