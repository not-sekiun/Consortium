from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class AssetListCommand(BaseCommand[ConnectedContext]):
    name = "as-list"
    description = "List all assets along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          as-list
        """,
    )
    group = "Asset Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            assets = await rest_api.get_all_assets()

            table = Table(title="Assets", highlight=True)
            table.add_column("Asset ID")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Size")
            for asset in assets:
                table.add_row(
                    asset["resource_id"],
                    asset["name"],
                    "DIRECTORY" if asset["is_directory"] else "FILE",
                    format_size_bytes_as_human_readable_str(size_bytes=asset["size"]),
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
