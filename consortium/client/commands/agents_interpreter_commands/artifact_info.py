from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_command_utils import display_agent_info
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console, print_warning


class ArtifactInfoCommand(BaseConnectedCommand):
    name = "ar-info"
    description = "Display information about an artifact by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          ar-info 123e4567-e89b-12d3-a456-42661417400
          ar-info 123e4567-e89b-12d3-a456-42661417400 --verbose  # Display agent information
        """,
    )
    group = "Artifact Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            help="Display verbose information about the agent that uploaded the artifact.",
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
        except SystemExit:
            pass

        return ContinueSignal()
