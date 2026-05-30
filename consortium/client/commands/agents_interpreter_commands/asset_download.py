import pathlib
import shutil
import tempfile
from argparse import ArgumentParser

from rich.progress import Progress

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class AssetDownloadCommand(BaseConnectedCommand):
    name = "as-dl"
    description = "Download an asset by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          as-dl 123e4567-e89b-12d3-a456-42661417400
          as-dl 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the asset if it is an asset directory.
        """,
    )
    group = "Asset Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_id",
            help="ID of the asset to download",
            nargs=1,
        )
        parser.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the asset file or directory to (defaults to "
                "current working directory with the assets name)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-d",
            "--decompress",
            help=(
                "Automatically decompress downloaded archive (.zip) asset directories "
                "(disabled by default). Does not decompress assets explicitly marked "
                "as files even if they are zip archives."
            ),
            action="store_true",
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
            # If user supplies a name that takes precedence, else use the asset name
            # directly for asset files or for asset directories append the ".zip" to the
            # name because all asset directories are returned as zip files.
            output_file_path = pathlib.Path(
                parsed_args.output
                if parsed_args.output
                else (
                    asset["name"]
                    if not asset["is_directory"]
                    else asset["name"] + ".zip"
                ),
            )

            if output_file_path.exists():
                print_error(
                    f"Cannot download asset to '{output_file_path}' because a file or "
                    f"directory already exists at that path"
                )
                return ContinueSignal()

            print_info(
                f"Downloading asset {'directory' if asset['is_directory'] else 'file'} "
                f"'{asset['name']}' ({asset['resource_id']}) to '{output_file_path}'..."
            )
            with Progress() as progress:
                downloading_task = progress.add_task(
                    "",
                    total=asset["size"],
                )
                with output_file_path.open("wb") as output_file:
                    async for chunk in rest_api.download_asset_by_asset_id(
                        asset_id=parsed_args.asset_id[0],
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
        except SystemExit:
            pass

        return ContinueSignal()
