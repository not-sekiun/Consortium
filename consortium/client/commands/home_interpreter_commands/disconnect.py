from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_connections_service = client_singletons.client_connections_service


class DisconnectCommand(BaseCommand):
    name = "disconnect"
    description = (
        "Disconnect the current client connection or a specific client connection from "
        "a Consortium server"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          disconnect  # Disconnects the current client connection if the client connection ID is not specified.
          disconnect 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help=(
                "The client connection ID of the client to disconnect. If not "
                "provided, the current client connection is disconnected."
            ),
            nargs="?",
            default=None,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            if parsed_args.client_connection_id is None:
                client_connection = command_context.environment["client_connection"]
            else:
                try:
                    client_connection = client_connections_service.get_client_connection_by_client_connection_id(
                        parsed_args.client_connection_id,
                    )
                except ValueError as exc:
                    print_error(str(exc))
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            await client_connection.logout()

            client_connections_service.remove_client_connection(
                client_connection,
            )
            print_success(
                f"Disconnected from server "
                f"{client_connection.remote_host}:{client_connection.remote_port} "
                f"with client connection: {client_connection}",
            )
            if client_connection == command_context.environment["client_connection"]:
                return ReturnStatus(type=ClientReturnStatusType.EXIT_CLIENT_CONNECTION)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
