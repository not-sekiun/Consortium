from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
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

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session = context.environment["client_session"]
            else:
                try:
                    client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            client_session_id=parsed_args.client_session_id,
                        )
                    )
                except ClientSessionNotFoundError as exc:
                    print_error(str(exc))
                    return ReturnStatus(type=ReturnStatusType.CONTINUE)

            # Store the previous client session string for the success
            # message to demonstrate the change in name.
            previous_client_session_str = str(client_session)
            client_session.name = parsed_args.name[0]
            print_success(
                f"Renamed client session {previous_client_session_str} to '{client_session.name}'"
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
