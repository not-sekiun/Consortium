from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ArtifactRemoveCommand(BaseConnectedCommand):
    name = "ar-rm"
    description = "Delete an artifact by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          ar-rm 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Artifact Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="The artifact's resource ID.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await rest_api.delete_artifact_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )
            print_success(f"Deleted artifact '{parsed_args.resource_id[0]}'")
        except SystemExit:
            pass

        return ContinueSignal()
