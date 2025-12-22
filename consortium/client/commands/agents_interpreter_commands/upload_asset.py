import pathlib
import shutil
import tempfile
from argparse import ArgumentParser

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class UploadAssetCommand(BaseCommand):
    name = "upload_asset"
    description = "Upload a specific asset."
    epilog = format_argparse_epilog(
        """
        Examples:
          upload_asset relative/path/to/asset_file.txt
          upload_asset /absolute/path/to/asset_directory
        """,
    )
    group = "Asset Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_path",
            help=(
                "The path of the asset to upload. This can be a path to a file or a "
                "directory."
            ),
            nargs=1,
        )
        parser.add_argument(
            "-n",
            "--name",
            help=(
                "The name to give the asset when being uploaded. By default this is "
                "the file or directory name."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-d",
            "--description",
            help="The description to give the asset when being uploaded.",
            nargs="?",
            default="",
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
            asset_path = pathlib.Path(parsed_args.asset_path[0])

            if not asset_path.exists():
                print_error(f"Asset path '{asset_path}' does not exist.")
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            if asset_path.is_dir():
                print_info(f"Uploading asset directory '{asset_path}'...")
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
                        asset = await client_rest_api_connection.upload_asset(
                            file_object=asset_file,
                            is_directory=True,
                            name=parsed_args.name
                            if parsed_args.name
                            else asset_path.name,
                            description=parsed_args.description,
                            asset_directory_archive_file_format=".zip",
                        )
                print_success(
                    f"Successfully uploaded asset directory '{asset_path}' as asset "
                    f"'{asset['name']}' ({asset['resource_id']}).",
                )
            else:
                print_info(f"Uploading asset file '{asset_path}'...")
                with asset_path.open("rb") as asset_file:
                    asset = await client_rest_api_connection.upload_asset(
                        file_object=asset_file,
                        is_directory=False,
                        name=parsed_args.name if parsed_args.name else asset_path.name,
                        description=parsed_args.description,
                    )
                print_success(
                    f"Successfully uploaded asset file '{asset_path}' as asset "
                    f"'{asset['name']}' ({asset['resource_id']}).",
                )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
