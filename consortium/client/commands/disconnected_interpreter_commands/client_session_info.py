from argparse import ArgumentParser

from consortium.client.models.context_models import DisconnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseDisconnectedCommand
from consortium.client.utils.client_session_command_utils import (
    display_client_session_info,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ClientSessionInfoCommand(BaseDisconnectedCommand):
    name = "info"
    description = "Display information for a client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "The client session ID of the client session to display detailed "
                "information for."
            ),
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "-p",
            "--password",
            help="Display the password of the client session.",
            action="store_true",
            default=False,
        )

    async def run(
        self,
        context: DisconnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            await display_client_session_info(
                client_session_id=parsed_args.client_session_id[0],
                show_password=parsed_args.password,
            )
        except SystemExit:
            pass

        return ContinueSignal()
