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
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class ArtifactDownloadCommand(BaseConnectedCommand):
    name = "ar-dl"
    description = "Download an artifact by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          ar-dl 123e4567-e89b-12d3-a456-42661417400
          ar-dl 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the artifact if it is an artifact directory.
        """,
    )
    group = "Artifact Management Commands"
    autocompletes = Autocomplete.ARTIFACT_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )
        parser.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the artifact file or directory to (defaults to "
                "the current working directory with the artifact's name)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-w",
            "--overwrite",
            help=(
                "Overwrite the output file if it already exists (disabled by default). "
                "Refuses to overwrite if the output path is an existing directory."
            ),
            action="store_true",
        )
        parser.add_argument(
            "-d",
            "--decompress",
            help=(
                "Automatically decompress downloaded archive (.zip) artifact directories "
                "(disabled by default). Does not decompress artifacts explicitly marked "
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

            artifact = await rest_api.get_artifact_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )
            # If user supplies an output path that takes precedence, else use the artifact
            # name directly for artifact files or append ".zip" for artifact directories
            # because all artifact directories are returned as zip files.
            output_file_path = pathlib.Path(
                parsed_args.output
                if parsed_args.output
                else (
                    artifact["name"]
                    if not artifact["is_directory"]
                    else artifact["name"] + ".zip"
                ),
            )

            if output_file_path.exists():
                # Refuse to overwrite a directory regardless of the overwrite flag as
                # clobbering a whole directory is never the intended download behaviour.
                if output_file_path.is_dir():
                    print_error(
                        f"Cannot download artifact to '{output_file_path}' because a "
                        f"directory already exists at that path"
                    )
                    return ContinueSignal()
                if not parsed_args.overwrite:
                    print_error(
                        f"Cannot download artifact to '{output_file_path}' because a file "
                        f"already exists at that path (use -w/--overwrite to overwrite "
                        f"it)"
                    )
                    return ContinueSignal()

            print_info(
                f"Downloading artifact {'directory' if artifact['is_directory'] else 'file'} "
                f"'{artifact['name']}' ({artifact['resource_id']}) to '{output_file_path}'..."
            )
            with Progress(transient=True) as progress:
                downloading_task = progress.add_task(
                    "",
                    total=artifact["size"],
                )
                with output_file_path.open("wb") as output_file:
                    async for chunk in rest_api.download_artifact_by_resource_id(
                        resource_id=parsed_args.resource_id[0],
                    ):
                        progress.update(downloading_task, advance=len(chunk))
                        output_file.write(chunk)
            print_success("Finished downloading artifact")

            if artifact["is_directory"] and parsed_args.decompress:
                print_info(f"Decompressing artifact directory: '{output_file_path}'")
                with tempfile.TemporaryDirectory() as temp_dir:
                    shutil.unpack_archive(output_file_path, temp_dir)
                    output_file_path.unlink()
                    shutil.move(temp_dir, output_file_path)
                print_success("Finished decompressing artifact")
        except SystemExit:
            pass

        return ContinueSignal()
