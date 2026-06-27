from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class PayloadRemoveCommand(BaseConnectedCommand):
    name = "pl-rm"
    description = "Delete a payload by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-rm 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Payload Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "payload_id",
            help="Payload ID of the payload to be removed.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await rest_api.delete_payload_by_payload_id(
                payload_id=parsed_args.payload_id[0],
            )
            print_success(f"Deleted payload '{parsed_args.payload_id[0]}'")
        except SystemExit:
            pass

        return ContinueSignal()
