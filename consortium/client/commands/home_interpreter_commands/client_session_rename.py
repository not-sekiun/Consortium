from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.client_session_command_utils import rename_client_session
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ClientSessionRenameCommand(BaseCommand):
    name = "rename"
    description = (
        "Set the name of the current client session, or a specific client session by "
        "its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          rename "New name"
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "ID of the client session to rename (defaults to the current client "
                "session if not provided)."
            ),
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "name",
            help="New name for the client session.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = context.client_session.client_session_id
            else:
                client_session_id = parsed_args.client_session_id[0]
            rename_client_session(
                client_session_id=client_session_id,
                name=parsed_args.name[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
