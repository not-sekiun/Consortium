from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


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

    @staticmethod
    def _rename_client_session(client_session_id: str, name: str) -> None:
        try:
            client_session = (
                client_sessions_service.get_client_session_by_client_session_id(
                    client_session_id=client_session_id,
                )
            )
            # Store the previous client session string for the success
            # message to demonstrate the change in name.
            previous_client_session_str = str(client_session)
            client_session.name = name
            print_success(
                f"Renamed client session {previous_client_session_str} to '{client_session.name}'"
            )
        except ClientSessionNotFoundError as exc:
            print_error(str(exc))

    async def run(self, context: Context) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = context.client_session.client_session_id
            else:
                client_session_id = parsed_args.client_session_id[0]
            self._rename_client_session(
                client_session_id=client_session_id,
                name=parsed_args.name[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
