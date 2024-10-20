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


class ListAssetsCommand(BaseCommand):
    name = "list_assets"
    description = "List all assets along with their essential information."
    epilog = format_argparse_epilog(
        """
        Examples:
          list_assets
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            assets = await client_rest_api_connection.get_all_assets()

            table = Table(title="Assets")
            table.add_column("Asset ID")
            table.add_column("Name")
            table.add_column("Description")
            table.add_column("Type")
            for asset in assets:
                table.add_row(
                    asset["resource_id"]
                    if asset["is_directory"]
                    else asset["resource_id"],
                    asset["name"],
                    asset["description"],
                    "Directory" if asset["is_directory"] else "File",
                )
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
