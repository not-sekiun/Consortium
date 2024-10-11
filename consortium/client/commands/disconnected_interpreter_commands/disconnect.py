from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class DisconnectCommand(BaseCommand):
    name = "disconnect"
    description = "Disconnect a specific client session from a Consortium server"
    epilog = format_argparse_epilog(
        """
        Examples:
          disconnect 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "The client session ID of the client to disconnect. If not "
                "provided, the current client session is disconnected."
            ),
            nargs=1,
            default=None,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            try:
                await client_sessions_service.disconnect_client_session(
                    client_session_id=parsed_args.client_session_id[0],
                )
            except ClientSessionNotFoundError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            client_session = (
                client_sessions_service.get_client_session_by_client_session_id(
                    client_session_id=parsed_args.client_session_id[0],
                )
            )

            print_success(
                f"Disconnected client session {client_session} from server "
                f"{client_session.remote_host}:{client_session.remote_port} ",
            )

            client_sessions_service.remove_client_session_by_client_session_id(
                client_session_id=str(client_session.client_session_id),
            )

            if client_session == command_context.environment["client_session"]:
                return ReturnStatus(type=ClientReturnStatusType.EXIT_CLIENT_SESSION)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
