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


class DisconnectCommand(BaseCommand):
    name = "disconnect"
    description = (
        "Disconnect the current client session or a specific client session from "
        "a Consortium server"
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
                "The client session ID of the client to disconnect. If not "
                "provided, the current client session is disconnected."
            ),
            nargs="?",
            default=None,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = str(
                    context.environment["client_session"].client_session_id,
                )
            else:
                client_session_id = parsed_args.client_session_id

            try:
                await client_sessions_service.disconnect_client_session(
                    client_session_id=client_session_id,
                )
            except ClientSessionNotFoundError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            client_session = (
                client_sessions_service.get_client_session_by_client_session_id(
                    client_session_id=client_session_id,
                )
            )

            print_success(
                f"Disconnected client session {client_session} from server "
                f"{client_session.remote_host}:{client_session.remote_port} ",
            )

            client_sessions_service.remove_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )

            if client_session == context.environment["client_session"]:
                return ReturnStatus(type=ReturnStatusType.EXIT_CLIENT_SESSION)
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
