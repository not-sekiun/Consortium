from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class AssetInfoCommand(BaseCommand[ConnectedContext]):
    name = "as-info"
    description = "Display information about an asset by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          as-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Asset Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_id",
            help="ID of the asset to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            asset = await rest_api.get_asset_by_asset_id(
                asset_id=parsed_args.asset_id[0],
            )
            table = Table(title="Asset Information", highlight=True)
            table.add_column("Information")
            table.add_column("Data")
            table.add_row("Resource ID", str(asset["resource_id"]))
            table.add_row("Name", str(asset["name"]))
            table.add_row("Description", str(asset["description"]))
            table.add_row(
                "Size",
                f"{asset['size']} ({format_size_bytes_as_human_readable_str(size_bytes=asset['size'])})",
            )
            table.add_row("Exists on disk", str(asset["exists_on_disk"]))
            table.add_row("MD5 Checksum", str(asset["md5_checksum"]))
            table.add_row(
                "Datetime Created",
                format_datetime_as_human_readable_str(
                    datetime_str=asset["datetime_created"], include_elapsed_time=True
                ),
            )
            table.add_row(
                "Datetime Updated",
                format_datetime_as_human_readable_str(
                    datetime_str=asset["datetime_modified"], include_elapsed_time=True
                ),
            )
            table.add_row("Type", "DIRECTORY" if asset["is_directory"] else "FILE")
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
