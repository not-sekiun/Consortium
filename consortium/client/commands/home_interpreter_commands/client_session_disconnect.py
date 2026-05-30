from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    ExitClientSessionSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.client_session_command_utils import (
    disconnect_client_session,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ClientSessionDisconnectCommand(BaseConnectedCommand):
    name = "disconnect"
    description = (
        "Disconnect the current client session or a specific client session by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          disconnect  # Disconnects the current client session if the client session ID is not specified.
          disconnect 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "ID of the client to disconnect (defaults to the current client "
                "session if not provided)."
            ),
            nargs="?",
            default=None,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = str(context.client_session.client_session_id)
            else:
                client_session_id = parsed_args.client_session_id

            await disconnect_client_session(client_session_id=client_session_id)

            if client_session_id == str(context.client_session.client_session_id):
                return ExitClientSessionSignal()
        except SystemExit:
            pass

        return ContinueSignal()
