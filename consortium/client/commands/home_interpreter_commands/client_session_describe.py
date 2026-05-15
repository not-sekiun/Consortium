from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.client_session_command_utils import describe_client_session


class ClientSessionDescribeCommand(BaseCommand):
    name = "describe"
    description = (
        "Set the description of the current client session or a specific client "
        "session by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          describe "New description" # Changes the description of the current client session if the client session ID is not specified.
          describe 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "ID of the client session whose description should be changed "
                "(defaults to the current client session if not specified)."
            ),
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "description",
            help="New description for the client session.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = context.client_session.client_session_id
            else:
                client_session_id = parsed_args.client_session_id[0]
            describe_client_session(
                client_session_id=client_session_id,
                description=parsed_args.description[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
