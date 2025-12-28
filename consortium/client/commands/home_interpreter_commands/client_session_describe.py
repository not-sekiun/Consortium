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
            help="New description to assign to the specified client session.",
            nargs=1,
        )

    @staticmethod
    async def _describe_client_session(
        client_session_id: str,
        description: str,
    ) -> None:
        client_session = (
            client_sessions_service.get_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )
        )
        client_session.description = description

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
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

            client_session.description = parsed_args.description[0]
            print_success(
                f"Updated {client_session} description to '{client_session.description}'"
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
