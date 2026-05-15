from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.client_session_command_utils import (
    display_client_session_info,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)


class ClientSessionInfoCommand(BaseCommand):
    name = "info"
    description = (
        "Display information for the current client session, or for a "
        "specific client session by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info -p  # Displays password
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "ID of the client session to display information for (defaults to the "
                "current client session if not provided)."
            ),
            nargs="?",
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
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            await display_client_session_info(
                client_session_id=context.client_session.client_session_id
                if parsed_args.client_session_id is None
                else parsed_args.client_session_id,
                show_password=parsed_args.password,
            )
        except SystemExit:
            pass

        return ContinueSignal()
