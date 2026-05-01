import pathlib
import shutil
import tempfile
from argparse import ArgumentParser

from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class AssetUploadCommand(BaseCommand):
    name = "up"
    description = "Upload an asset file or directory from its file or directory path"
    epilog = format_argparse_epilog(
        """
        Examples:
          up relative/path/to/asset_file.txt
          up /absolute/path/to/asset_directory
        """,
    )
    group = "Asset Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_path",
            help="Relative or absolute path to the file or directory to upload.",
            nargs=1,
        )
        parser.add_argument(
            "-n",
            "--name",
            help=(
                "Name to give the asset when uploaded (defaults to the file or "
                "directory name)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-d",
            "--description",
            help="Description for the asset.",
            nargs="?",
            default="",
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            asset_path = pathlib.Path(parsed_args.asset_path[0])

            if not asset_path.exists():
                print_error(f"Asset path not found: '{asset_path}'")
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
                            name=parsed_args.name
                            if parsed_args.name
                            else asset_path.name,
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
        except SystemExit:
            pass

        return ContinueSignal()
