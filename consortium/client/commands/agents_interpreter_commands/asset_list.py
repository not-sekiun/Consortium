from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class AssetListCommand(BaseConnectedCommand):
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
            table.add_column("Resource ID")
            table.add_column("Name")
            table.add_column("Uploaded By")
            table.add_column("Type")
            table.add_column("Size")
            for asset in assets:
                size = asset["size"]
                # An asset is "just" a resource with metadata: the uploading user
                # account is carried in the `data` field. The stored reference records
                # only the username as of upload; the live `resolved_user_account`
                # (when present) supplies the account's current ID and proves it still
                # exists, while its absence means the account has since been deleted.
                user_account = (asset["data"] or {}).get("user_account")
                resolved_user_account = (asset["data"] or {}).get(
                    "resolved_user_account"
                )
                if user_account is None:
                    uploaded_by = "N/A"
                elif resolved_user_account is not None:
                    uploaded_by = (
                        f"{user_account['username']} "
                        f"({resolved_user_account['user_account_id']})"
                    )
                else:
                    uploaded_by = (
                        f"{user_account['username']} [account no longer exists]"
                    )
                table.add_row(
                    asset["resource_id"],
                    asset["name"],
                    uploaded_by,
                    "DIRECTORY" if asset["is_directory"] else "FILE",
                    format_size_bytes_as_human_readable_str(size_bytes=size)
                    if size is not None
                    else "N/A",
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
