from argparse import ArgumentParser

from consortium.client.commands.home_interpreter_commands.client_session_disconnect import (
    ClientSessionDisconnectCommand as HomeInterpreterClientSessionDisconnectCommand,
)
from consortium.client.models.context_model import AnyContext, ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    ExitClientSessionSignal,
    InterpreterSignal,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ClientSessionDisconnectCommand(HomeInterpreterClientSessionDisconnectCommand):
    name = "disconnect"
    description = "Disconnect a specific client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          disconnect 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help="ID of the client session to disconnect.",
            nargs=1,
            default=None,
        )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            client_session_id = parsed_args.client_session_id[0]
            await self._disconnect_client_session(
                client_session_id=client_session_id,
            )

            if isinstance(context, ConnectedContext) and client_session_id == str(
                context.client_session.client_session_id
            ):
                return ExitClientSessionSignal()
        except SystemExit:
            pass

        return ContinueSignal()
