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
    description = "Disconnect a specific client connection from a Consortium server."
    epilog = format_argparse_epilog(
        """
        Examples:
          disconnect 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help="The client connection ID of the client connection to disconnect.",
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
                client_connection = client_connections_service.get_client_connection_by_client_connection_id(
                    parsed_args.client_connection_id[0],
                )
            except ValueError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            await client_connection.disconnect()
            client_connections_service.remove_client_connection(
                client_connection,
            )
            print_success(
                f"Disconnected from server "
                f"{client_connection.remote_host}:{client_connection.remote_port} "
                f"with client connection: {client_connection}",
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
