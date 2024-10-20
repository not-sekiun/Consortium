from argparse import ArgumentParser

from rich.table import Table

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE


class InfoAssetCommand(BaseCommand):
    name = "info_asset"
    description = "Display detailed information about a specific asset."
    epilog = format_argparse_epilog(
        """
        Examples:
          info_asset 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_id",
            help="The asset ID of the asset to display detailed information for.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            asset = await client_rest_api_connection.get_asset_by_asset_id(
                asset_id=parsed_args.asset_id[0],
            )

            if not asset["is_directory"]:
                table = Table(title="Asset Information")
                table.add_column("Information")
                table.add_column("Data")
                table.add_row("Resource ID", asset["resource_id"])
                table.add_row("Name", asset["name"])
                table.add_row("Description", asset["description"])
                table.add_row("Size", str(asset["size"]))
                table.add_row("Exists on disk", str(asset["exists_on_disk"]))
                table.add_row("MD5 Checksum", asset["md5_checksum"])
                table.add_row("Datetime Created", asset["datetime_created"])
                table.add_row("Datetime Updated", asset["datetime_updated"])
                table.add_row("Is Directory", str(asset["is_directory"]))
            else:
                table = Table(title="Asset Information")
                table.add_column("Information")
                table.add_column("Data")
                table.add_row("Resource ID", asset["resource_id"])
                table.add_row("Name", asset["name"])
                table.add_row("Description", asset["description"])
                table.add_row("Size", str(asset["size"]))
                table.add_row("Exists on disk", str(asset["exists_on_disk"]))
                table.add_row("Datetime Created", asset["datetime_created"])
                table.add_row("Datetime Updated", asset["datetime_updated"])
                table.add_row("Is Directory", str(asset["is_directory"]))
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
