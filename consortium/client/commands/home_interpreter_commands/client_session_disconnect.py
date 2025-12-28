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


class ClientSessionDisconnectCommand(BaseCommand):
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

    @staticmethod
    async def _disconnect_client_session(
        client_session_id: str,
    ) -> None:
        try:
            client_session = (
                client_sessions_service.get_client_session_by_client_session_id(
                    client_session_id=client_session_id,
                )
            )
            await client_sessions_service.remove_client_session_by_client_session_id(
                client_session_id=client_session_id,
            )
            print_success(
                f"Disconnected {client_session} from server "
                f"{client_session.remote_host}:{client_session.remote_port}"
            )
        except ClientSessionNotFoundError as exc:
            print_error(str(exc))

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                client_session_id = str(context.client_session.client_session_id)
            else:
                client_session_id = parsed_args.client_session_id

            await self._disconnect_client_session(client_session_id=client_session_id)

            if client_session_id == str(context.client_session.client_session_id):
                return ReturnStatus(type=ReturnStatusType.EXIT_CLIENT_SESSION)
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
