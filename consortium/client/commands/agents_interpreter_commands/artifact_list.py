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


class ArtifactListCommand(BaseConnectedCommand):
    name = "ar-list"
    description = "List all artifacts along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          ar-list
        """,
    )
    group = "Artifact Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            artifacts = await rest_api.get_all_artifacts()

            table = Table(title="Artifacts", highlight=True)
            table.add_column("Artifact ID")
            table.add_column("Name")
            table.add_column("Produced By")
            table.add_column("Type")
            table.add_column("Size")
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
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
