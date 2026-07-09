from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class AssetInfoCommand(BaseConnectedCommand):
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
            # An asset is "just" a repository resource with attached metadata. The
            # resource fields describe the file/directory on disk while the `data` field
            # holds the asset specific metadata (for example the uploading user account).
            size = asset["size"]
            # The stored `user_account` reference is an immutable point-in-time record of
            # the uploading account (its username and role as of upload). It deliberately
            # does not persist a user account ID, since those are reissued across restarts.
            # The live `resolved_user_account` (when present) supplies the account's
            # current ID, proving it still exists; its absence means the account that
            # uploaded the asset has since been deleted.
            user_account = asset["data"]["user_account"]
            resolved_user_account = asset["data"]["resolved_user_account"]

            if user_account is None:
                uploaded_by = "N/A"
            elif resolved_user_account is not None:
                uploaded_by = (
                    f"{user_account['username']} "
                    f"({resolved_user_account['user_account_id']}) "
                    f"with role '{user_account['role']}'"
                )
            else:
                uploaded_by = (
                    f"{user_account['username']} with role '{user_account['role']}' "
                    f"[account no longer exists]"
                )

            table = Table(title="Asset Information", highlight=True)
            table.add_column("Information")
            table.add_column("Data")
            table.add_row("Resource ID", str(asset["resource_id"]))
            table.add_row("Name", str(asset["name"]))
            table.add_row("Description", str(asset["description"]))
            table.add_row("Extension", str(asset["extension"]))
            table.add_row(
                "Size",
                f"{size} B ({format_size_bytes_as_human_readable_str(size_bytes=size)})"
                if size is not None
                else "N/A",
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
                "Datetime Modified",
                format_datetime_as_human_readable_str(
                    datetime_str=asset["datetime_modified"], include_elapsed_time=True
                ),
            )
            table.add_row("Type", "DIRECTORY" if asset["is_directory"] else "FILE")
            table.add_row("Uploaded By", uploaded_by)
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
