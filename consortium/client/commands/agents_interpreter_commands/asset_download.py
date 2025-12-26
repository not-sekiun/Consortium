import pathlib
import shutil
import tempfile
from argparse import ArgumentParser

from rich.progress import Progress

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


class AssetDownloadCommand(BaseCommand):
    name = "as-dl"
    description = "Download an asset by its asset ID"
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
                    "directory already exists at that path.",
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            print_info(
                f"Downloading asset {'directory' if asset['is_directory'] else 'file'} "
                f"'{asset['name']}' ({asset['resource_id']}) to "
                f"'{output_file_path}'...",
            )
            with Progress() as progress:
                downloading_task = progress.add_task(
                    "",
                    total=asset["size"],
                )
                with output_file_path.open("wb") as output_file:
                    async for (
                        chunk
                    ) in client_rest_api_connection.download_asset_by_asset_id(
                        asset_id=parsed_args.asset_id[0],
                    ):
                        progress.update(downloading_task, advance=len(chunk))
                        output_file.write(chunk)
            print_success("Finished downloading.")

            if asset["is_directory"] and parsed_args.decompress:
                print_info(
                    f"Decompressing asset directory '{output_file_path}'...",
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    shutil.unpack_archive(output_file_path, temp_dir)
                    output_file_path.unlink()
                    shutil.move(temp_dir, output_file_path)
                print_success("Finished decompression.")
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
