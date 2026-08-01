import pathlib
import shutil
import tempfile
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

from prompt_toolkit.completion import PathCompleter
from rich.progress import Progress
from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.environment_utils import (
    print_containerized_missing_path_notice,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import (
    console,
    print_error,
    print_info,
    print_success,
)


class AssetCommand(BaseConnectedCommand):
    name = "asset"
    description = "Manage assets through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          asset list
          asset info 123e4567-e89b-12d3-a456-42661417400
          asset upload relative/path/to/asset_file.txt
          asset download 123e4567-e89b-12d3-a456-42661417400
          asset rename 123e4567-e89b-12d3-a456-42661417400 "New name"
          asset describe 123e4567-e89b-12d3-a456-42661417400 "New description"
          asset remove 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            asset download --help
        """,
    )
    group = "Resource Management Commands"
    autocompletes = {
        "list": None,
        "info": Autocomplete.ASSET_ID,
        "upload": PathCompleter(),
        "download": Autocomplete.ASSET_ID,
        "rename": Autocomplete.ASSET_ID,
        "describe": Autocomplete.ASSET_ID,
        "remove": Autocomplete.ASSET_ID,
    }

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help="List all assets along with their essential information.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset list
                """,
            ),
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help="Display information about an asset by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset info 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser_info.add_argument(
            "resource_id",
            help="The asset's resource ID.",
            nargs=1,
        )

        # upload sub-command
        parser_upload = subparsers.add_parser(
            "upload",
            help="Upload an asset file or directory from its file or directory path.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset upload relative/path/to/asset_file.txt
                  asset upload /absolute/path/to/asset_directory
                """,
            ),
        )
        parser_upload.add_argument(
            "asset_path",
            help="Relative or absolute path to the file or directory to upload.",
            nargs=1,
        )
        parser_upload.add_argument(
            "-n",
            "--name",
            help=(
                "Name to give the asset when uploaded (defaults to the file or "
                "directory name)."
            ),
            nargs="?",
        )
        parser_upload.add_argument(
            "-d",
            "--description",
            help="Description for the asset.",
            nargs="?",
            default="",
        )

        # download sub-command
        parser_download = subparsers.add_parser(
            "download",
            help="Download an asset by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset download 123e4567-e89b-12d3-a456-42661417400
                  asset download 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the asset if it is an asset directory.
                """,
            ),
        )
        parser_download.add_argument(
            "resource_id",
            help="The asset's resource ID.",
            nargs=1,
        )
        parser_download.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the asset file or directory to (defaults to "
                "current working directory with the assets name)."
            ),
            nargs="?",
        )
        parser_download.add_argument(
            "-w",
            "--overwrite",
            help=(
                "Overwrite the output file if it already exists (disabled by default). "
                "Refuses to overwrite if the output path is an existing directory."
            ),
            action="store_true",
        )
        parser_download.add_argument(
            "-d",
            "--decompress",
            help=(
                "Automatically decompress downloaded archive (.zip) asset directories "
                "(disabled by default). Does not decompress assets explicitly marked "
                "as files even if they are zip archives."
            ),
            action="store_true",
        )

        # rename sub-command
        parser_rename = subparsers.add_parser(
            "rename",
            help="Set the name of an asset by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset rename 123e4567-e89b-12d3-a456-42661417400 "New name"
                """,
            ),
        )
        parser_rename.add_argument(
            "resource_id",
            help="The asset's resource ID.",
            nargs=1,
        )
        parser_rename.add_argument(
            "name",
            help="New name for the asset.",
            nargs=1,
        )

        # describe sub-command
        parser_describe = subparsers.add_parser(
            "describe",
            help="Set the description of an asset by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset describe 123e4567-e89b-12d3-a456-42661417400 "New description"
                """,
            ),
        )
        parser_describe.add_argument(
            "resource_id",
            help="The resource ID of the asset whose description should be changed.",
            nargs=1,
        )
        parser_describe.add_argument(
            "description",
            help="New description for the asset.",
            nargs=1,
        )

        # remove sub-command
        parser_remove = subparsers.add_parser(
            "remove",
            help="Delete an asset by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  asset remove 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser_remove.add_argument(
            "resource_id",
            help="The asset's resource ID.",
            nargs=1,
        )

    @staticmethod
    async def _handle_list_sub_command(
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        assets = await rest_api.get_all_assets()

        table = Table(title="Assets", highlight=True)
        table.add_column("Resource ID")
        table.add_column("Name")
        table.add_column("Uploaded By")
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("Datetime Created")
        for asset in assets:
            size = asset["size"]
            # An asset is "just" a resource with metadata: the uploading user
            # account is carried in the `data` field. The stored reference records
            # only the username as of upload; the live `resolved_user_account`
            # (when present) supplies the account's current ID and proves it still
            # exists, while its absence means the account has since been deleted.
            user_account = (asset["data"] or {}).get("user_account")
            resolved_user_account = (asset["data"] or {}).get("resolved_user_account")
            if user_account is None:
                uploaded_by = "N/A"
            elif resolved_user_account is not None:
                uploaded_by = (
                    f"{user_account['username']} "
                    f"({resolved_user_account['user_account_id']})"
                )
            else:
                uploaded_by = f"{user_account['username']} [account no longer exists]"
            table.add_row(
                asset["resource_id"],
                asset["name"],
                uploaded_by,
                "DIRECTORY" if asset["is_directory"] else "FILE",
                format_size_bytes_as_human_readable_str(size_bytes=size)
                if size is not None
                else "N/A",
                format_datetime_as_human_readable_str(
                    datetime_str=asset["datetime_created"],
                    include_elapsed_time=True,
                ),
            )
        console.print(table, "")

        return ContinueSignal()

    @staticmethod
    async def _handle_info_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        asset = await rest_api.get_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
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

        return ContinueSignal()

    @staticmethod
    async def _handle_upload_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api
        asset_path = pathlib.Path(parsed_args.asset_path[0])

        if not asset_path.exists():
            print_error(f"Asset path not found: '{asset_path}'")
            print_containerized_missing_path_notice(path=asset_path)
            return ContinueSignal()

        if asset_path.is_dir():
            print_info(f"Uploading asset directory: '{asset_path}'")
            with tempfile.TemporaryDirectory() as temp_dir_path:
                # When the archive file is created by `shutil.make_archive`, the
                # .zip file extension is appended automatically as inferred from the
                # `format` parameter.
                temp_archive_file = pathlib.Path(temp_dir_path, "archive")
                shutil.make_archive(
                    base_name=str(temp_archive_file.resolve()),
                    format="zip",
                    root_dir=asset_path,
                )
                # The actual `temp_archive_file` file path object does not include
                # the .zip file extension.
                with temp_archive_file.with_suffix(".zip").open("rb") as asset_file:
                    asset = await rest_api.upload_asset(
                        file_object=asset_file,
                        is_directory=True,
                        name=parsed_args.name if parsed_args.name else asset_path.name,
                        description=parsed_args.description,
                        asset_directory_archive_file_format=".zip",
                    )
            print_success(
                f"Uploaded asset directory '{asset_path}' as: "
                f"'{asset['name']}' ({asset['resource_id']})"
            )
        else:
            print_info(f"Uploading asset file: '{asset_path}'")
            with asset_path.open("rb") as asset_file:
                asset = await rest_api.upload_asset(
                    file_object=asset_file,
                    is_directory=False,
                    name=parsed_args.name if parsed_args.name else asset_path.name,
                    description=parsed_args.description,
                )
            print_success(
                f"Uploaded asset file '{asset_path}' as: "
                f"'{asset['name']}' ({asset['resource_id']})"
            )

        return ContinueSignal()

    @staticmethod
    async def _handle_download_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        asset = await rest_api.get_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        # If user supplies a name that takes precedence, else use the asset name
        # directly for asset files or for asset directories append the ".zip" to the
        # name because all asset directories are returned as zip files. Resolved so
        # that every message below names the exact location written to: a bare relative
        # name reads as if the file landed next to the user, which is misleading when
        # the client runs in a container and the working directory is a container path.
        output_file_path = pathlib.Path(
            parsed_args.output
            if parsed_args.output
            else (
                asset["name"] if not asset["is_directory"] else asset["name"] + ".zip"
            ),
        ).resolve()

        if output_file_path.exists():
            # Refuse to overwrite a directory regardless of the overwrite flag as
            # clobbering a whole directory is never the intended download behaviour.
            if output_file_path.is_dir():
                print_error(
                    f"Cannot download asset to '{output_file_path}' because a "
                    f"directory already exists at that path"
                )
                return ContinueSignal()
            if not parsed_args.overwrite:
                print_error(
                    f"Cannot download asset to '{output_file_path}' because a file "
                    f"already exists at that path (use -w/--overwrite to overwrite "
                    f"it)"
                )
                return ContinueSignal()

        print_info(
            f"Downloading asset {'directory' if asset['is_directory'] else 'file'} "
            f"'{asset['name']}' ({asset['resource_id']}) to '{output_file_path}'..."
        )
        with Progress(transient=True) as progress:
            downloading_task = progress.add_task(
                "",
                total=asset["size"],
            )
            with output_file_path.open("wb") as output_file:
                async for chunk in rest_api.download_asset_by_resource_id(
                    resource_id=parsed_args.resource_id[0],
                ):
                    progress.update(downloading_task, advance=len(chunk))
                    output_file.write(chunk)
        print_success("Finished downloading asset")

        if asset["is_directory"] and parsed_args.decompress:
            print_info(f"Decompressing asset directory: '{output_file_path}'")
            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.unpack_archive(output_file_path, temp_dir)
                output_file_path.unlink()
                shutil.move(temp_dir, output_file_path)
            print_success("Finished decompressing asset")

        return ContinueSignal()

    @staticmethod
    async def _handle_rename_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        # The asset is fetched first purely so that the previous name can be shown
        # back to the operator alongside the new one.
        asset = await rest_api.get_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        await rest_api.update_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
            new_asset_attributes={"name": parsed_args.name[0]},
        )
        print_success(
            f"Renamed asset '{asset['name']}' ({asset['resource_id']}) to "
            f"'{parsed_args.name[0]}'",
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_describe_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        # The asset is fetched first purely so that its name can be shown back to the
        # operator alongside its resource ID.
        asset = await rest_api.get_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        await rest_api.update_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
            new_asset_attributes={"description": parsed_args.description[0]},
        )
        print_success(
            f"Updated description of asset '{asset['name']}' "
            f"({asset['resource_id']}) to '{parsed_args.description[0]}'",
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_remove_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        await rest_api.delete_asset_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        print_success(f"Deleted asset '{parsed_args.resource_id[0]}'")

        return ContinueSignal()

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "list":
                    return await self._handle_list_sub_command(context=context)
                case "info":
                    return await self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "upload":
                    return await self._handle_upload_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "download":
                    return await self._handle_download_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "rename":
                    return await self._handle_rename_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "describe":
                    return await self._handle_describe_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "remove":
                    return await self._handle_remove_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown asset sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
