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
from consortium.client.utils.printer_utils import print_error, print_success
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class DisconnectCommand(BaseCommand):
    name = "disconnect"
    description = (
        "Disconnect from the current client connection or a specific client connection."
    )
    epilog = argparse_epilog_formatter(
        """
        Example:
            disconnect  # Disconnect the current client connection
            disconnect 123e4567-e89b-12d3-a456-42661417400  # Disconnect the client connection with client connection ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help="Client connection ID of the client connection to disconnect. If no client connection ID is provided, the current client connection is disconnected.",
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
                target_client_connection = command_context.environment[
                    "client_connection"
                ]
            else:
                try:
                    target_client_connection = client_connections_service.get_client_connection_by_client_connection_id(
                        parsed_args.client_connection_id,
                    )
                except ValueError as exc:
                    print_error(str(exc))
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            await target_client_connection.logout()
            client_connections_service.remove_client_connection(
                target_client_connection,
            )
            print_success(
                f"Disconnected client connection: {target_client_connection}",
            )

            if (
                target_client_connection
                == command_context.environment["client_connection"]
            ):
                return ReturnStatus(type=ClientReturnStatusType.EXIT_CLIENT_CONNECTION)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
