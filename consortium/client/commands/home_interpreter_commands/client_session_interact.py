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


class InteractClientSessionCommand(BaseCommand):
    name = "interact"
    description = "Interact with a client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          interact 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help="ID of the client session to interact with.",
            nargs=1,
            default=None,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            try:
                client_session = (
                    client_sessions_service.get_client_session_by_client_session_id(
                        parsed_args.client_session_id[0],
                    )
                )
            except ClientSessionNotFoundError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            if client_session == context.environment["client_session"]:
                print_error(f"Already interacting with client session {client_session}")
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            print_success(f"Interacting with client session {client_session}")

            return ReturnStatus(
                type=ReturnStatusType.SWITCH_CLIENT_SESSION,
                data={
                    "client_session": client_session,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
