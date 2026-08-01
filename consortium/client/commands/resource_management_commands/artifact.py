import pathlib
import shutil
import tempfile
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

from rich.progress import Progress
from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_command_utils import display_agent_info
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
    print_warning,
)


class ArtifactCommand(BaseConnectedCommand):
    name = "artifact"
    description = "Manage artifacts through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          artifact list
          artifact info 123e4567-e89b-12d3-a456-42661417400
          artifact download 123e4567-e89b-12d3-a456-42661417400
          artifact rename 123e4567-e89b-12d3-a456-42661417400 "New name"
          artifact describe 123e4567-e89b-12d3-a456-42661417400 "New description"
          artifact remove 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            artifact download --help
        """,
    )
    group = "Resource Management Commands"
    autocompletes = {
        "list": None,
        "info": Autocomplete.ARTIFACT_ID,
        "download": Autocomplete.ARTIFACT_ID,
        "rename": Autocomplete.ARTIFACT_ID,
        "describe": Autocomplete.ARTIFACT_ID,
        "remove": Autocomplete.ARTIFACT_ID,
    }

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help="List all artifacts along with their essential information.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact list
                """,
            ),
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help="Display information about an artifact by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact info 123e4567-e89b-12d3-a456-42661417400
                  artifact info 123e4567-e89b-12d3-a456-42661417400 --verbose  # Display agent information
                """,
            ),
        )
        parser_info.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )
        parser_info.add_argument(
            "-v",
            "--verbose",
            help=(
                "Display verbose information about the agent that uploaded the "
                "artifact."
            ),
            action="store_true",
        )

        # download sub-command
        parser_download = subparsers.add_parser(
            "download",
            help="Download an artifact by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact download 123e4567-e89b-12d3-a456-42661417400
                  artifact download 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the artifact if it is an artifact directory.
                """,
            ),
        )
        parser_download.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )
        parser_download.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the artifact file or directory to (defaults to "
                "the current working directory with the artifact's name)."
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
                "Automatically decompress downloaded archive (.zip) artifact "
                "directories (disabled by default). Does not decompress artifacts "
                "explicitly marked as files even if they are zip archives."
            ),
            action="store_true",
        )

        # rename sub-command
        parser_rename = subparsers.add_parser(
            "rename",
            help="Set the name of an artifact by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact rename 123e4567-e89b-12d3-a456-42661417400 "New name"
                """,
            ),
        )
        parser_rename.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )
        parser_rename.add_argument(
            "name",
            help="New name for the artifact.",
            nargs=1,
        )

        # describe sub-command
        parser_describe = subparsers.add_parser(
            "describe",
            help="Set the description of an artifact by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact describe 123e4567-e89b-12d3-a456-42661417400 "New description"
                """,
            ),
        )
        parser_describe.add_argument(
            "resource_id",
            help="The resource ID of the artifact whose description should be changed.",
            nargs=1,
        )
        parser_describe.add_argument(
            "description",
            help="New description for the artifact.",
            nargs=1,
        )

        # remove sub-command
        parser_remove = subparsers.add_parser(
            "remove",
            help="Delete an artifact by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  artifact remove 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser_remove.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )

    @staticmethod
    async def _handle_list_sub_command(
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        artifacts = await rest_api.get_all_artifacts()

        table = Table(title="Artifacts", highlight=True)
        table.add_column("Artifact ID")
        table.add_column("Name")
        table.add_column("Produced By")
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("Datetime Created")
        for artifact in artifacts:
            size = artifact["size"]
            # An artifact is "just" a resource with metadata: the producing agent is
            # carried in the `data` field.
            agent = (artifact["data"] or {}).get("agent")
            table.add_row(
                artifact["resource_id"],
                artifact["name"],
                agent["name"] if agent else "N/A",
                "DIRECTORY" if artifact["is_directory"] else "FILE",
                format_size_bytes_as_human_readable_str(size_bytes=size)
                if size is not None
                else "N/A",
                format_datetime_as_human_readable_str(
                    datetime_str=artifact["datetime_created"],
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

        artifact = await rest_api.get_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        # An artifact is "just" a repository resource with attached metadata. The
        # resource fields describe the file/directory on disk while the `data` field
        # holds the artifact specific metadata (for example the producing agent).
        size = artifact["size"]
        agent = artifact["data"]["agent"]
        resolved_agent = artifact["data"]["resolved_agent"]

        table = Table(title="Artifact Information", highlight=True)
        table.add_column("Information")
        table.add_column("Data")
        table.add_row("Resource ID", str(artifact["resource_id"]))
        table.add_row("Name", str(artifact["name"]))
        table.add_row("Description", str(artifact["description"]))
        table.add_row("Extension", str(artifact["extension"]))
        table.add_row(
            "Size",
            f"{size} B ({format_size_bytes_as_human_readable_str(size_bytes=size)})"
            if size is not None
            else "N/A",
        )
        table.add_row("Exists on disk", str(artifact["exists_on_disk"]))
        table.add_row("MD5 Checksum", str(artifact["md5_checksum"]))
        table.add_row(
            "Datetime Created",
            format_datetime_as_human_readable_str(
                datetime_str=artifact["datetime_created"], include_elapsed_time=True
            ),
        )
        table.add_row(
            "Datetime Modified",
            format_datetime_as_human_readable_str(
                datetime_str=artifact["datetime_modified"],
                include_elapsed_time=True,
            ),
        )
        table.add_row("Type", "DIRECTORY" if artifact["is_directory"] else "FILE")
        table.add_row(
            "Produced By Agent",
            f"{agent['name']} ({agent['agent_id']}) of type '{agent['agent_type']}'"
            if agent
            else "N/A",
        )
        console.print(table, "")

        if parsed_args.verbose:
            # The producing agent reference stored on an artifact is an immutable
            # point-in-time tag; the agent it names may since have been deleted.
            # `resolved_agent` is the live resolution of that reference (or None when
            # it can no longer be resolved), so guard for its absence and inform the
            # user rather than rendering an empty table.
            if resolved_agent is not None:
                display_agent_info(agent=resolved_agent, verbose=False)
            else:
                print_warning(
                    "The agent that produced this artifact no longer exists; "
                    "its detailed information cannot be displayed."
                )

        return ContinueSignal()

    @staticmethod
    async def _handle_download_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        artifact = await rest_api.get_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        # If user supplies an output path that takes precedence, else use the artifact
        # name directly for artifact files or append ".zip" for artifact directories
        # because all artifact directories are returned as zip files. Resolved so that
        # every message below names the exact location written to: a bare relative name
        # reads as if the file landed next to the user, which is misleading when the
        # client runs in a container and the working directory is a container path.
        output_file_path = pathlib.Path(
            parsed_args.output
            if parsed_args.output
            else (
                artifact["name"]
                if not artifact["is_directory"]
                else artifact["name"] + ".zip"
            ),
        ).resolve()

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

        return ContinueSignal()

    @staticmethod
    async def _handle_rename_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        # The artifact is fetched first purely so that the previous name can be shown
        # back to the operator alongside the new one.
        artifact = await rest_api.get_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        await rest_api.update_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
            new_artifact_attributes={"name": parsed_args.name[0]},
        )
        print_success(
            f"Renamed artifact '{artifact['name']}' ({artifact['resource_id']}) to "
            f"'{parsed_args.name[0]}'",
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_describe_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        # The artifact is fetched first purely so that its name can be shown back to
        # the operator alongside its resource ID.
        artifact = await rest_api.get_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        await rest_api.update_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
            new_artifact_attributes={"description": parsed_args.description[0]},
        )
        print_success(
            f"Updated description of artifact '{artifact['name']}' "
            f"({artifact['resource_id']}) to '{parsed_args.description[0]}'",
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_remove_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        await rest_api.delete_artifact_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        print_success(f"Deleted artifact '{parsed_args.resource_id[0]}'")

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
                        f"Unknown artifact sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
