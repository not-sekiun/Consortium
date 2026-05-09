from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.home_interpreter_commands.client_session_describe import (
    ClientSessionDescribeCommand as HomeInterpreterClientSessionDescribeCommand,
)
from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog

client_sessions_service = client_singletons.client_sessions_service


class ClientSessionDescribeCommand(HomeInterpreterClientSessionDescribeCommand):
    name = "describe"
    description = "Set the description of a client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          describe 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help="ID of the client session whose description should be changed.",
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "description",
            help="New description for the client session.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            self._describe_client_session(
                client_session_id=parsed_args.client_session_id[0],
                description=parsed_args.description[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
