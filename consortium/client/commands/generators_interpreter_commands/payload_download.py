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


class PayloadDownloadCommand(BaseConnectedCommand):
    name = "pl-dl"
    description = "Download a payload by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-dl 123e4567-e89b-12d3-a456-42661417400
          pl-dl 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the payload if it is a payload directory.
        """,
    )
    group = "Payload Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="Resource ID of the payload to download.",
            nargs=1,
        )
        parser.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the payload file or directory to (defaults to "
                "the current working directory with the payload's name)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-d",
            "--decompress",
            help=(
                "Automatically decompress downloaded archive (.zip) payload directories "
                "(disabled by default). Does not decompress payloads explicitly marked "
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

            payload = await rest_api.get_payload_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )
            # If user supplies an output path that takes precedence, else use the payload
            # name directly for payload files or append ".zip" for payload directories
            # because all payload directories are returned as zip files.
            output_file_path = pathlib.Path(
                parsed_args.output
                if parsed_args.output
                else (
                    payload["name"]
                    if not payload["is_directory"]
                    else payload["name"] + ".zip"
                ),
            )

            if output_file_path.exists():
                print_error(
                    f"Cannot download payload to '{output_file_path}' because a file or "
                    f"directory already exists at that path"
                )
                return ContinueSignal()

            print_info(
                f"Downloading payload {'directory' if payload['is_directory'] else 'file'} "
                f"'{payload['name']}' ({payload['resource_id']}) to '{output_file_path}'..."
            )
            with Progress() as progress:
                downloading_task = progress.add_task(
                    "",
                    total=payload["size"],
                )
                with output_file_path.open("wb") as output_file:
                    async for chunk in rest_api.download_payload_by_resource_id(
                        resource_id=parsed_args.resource_id[0],
                    ):
                        progress.update(downloading_task, advance=len(chunk))
                        output_file.write(chunk)
            print_success("Finished downloading payload")

            if payload["is_directory"] and parsed_args.decompress:
                print_info(f"Decompressing payload directory: '{output_file_path}'")
                with tempfile.TemporaryDirectory() as temp_dir:
                    shutil.unpack_archive(output_file_path, temp_dir)
                    output_file_path.unlink()
                    shutil.move(temp_dir, output_file_path)
                print_success("Finished decompressing payload")
        except SystemExit:
            pass

        return ContinueSignal()
