from argparse import ArgumentParser

from consortium.client.models.context_models import DisconnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.client_session_command_utils import rename_client_session
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ClientSessionRenameCommand(BaseCommand[DisconnectedContext]):
    name = "rename"
    description = "Set the name of a specific client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help="ID of the client session to rename.",
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "name",
            help="New name for the client session.",
            nargs=1,
        )

    async def run(
        self,
        context: DisconnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rename_client_session(
                client_session_id=parsed_args.client_session_id[0],
                name=parsed_args.name[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
