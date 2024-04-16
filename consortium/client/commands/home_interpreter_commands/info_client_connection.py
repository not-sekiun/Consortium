from argparse import ArgumentParser

from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE, print_error
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class InfoClientConnectionCommand(BaseCommand):
    name = "info_client_connection"
    description = "List all information for the current client connection or for a specific client connection by its client connection ID."
    epilog = argparse_epilog_formatter(
        """
        Example:
            info_client_session  # Displayinformation for the current client session
            info_client_session 123e4567-e89b-12d3-a456-42661417400  # Displayinformation for the client session with client session ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help="Client connection ID of the client connection to display information for. If not provided, information for the current client connection is displayed",
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

            role = (await client_connection.get_own_user_info())["role"]

            table = Table(title="Client Connection Info")

            table.add_column("Information")
            table.add_column("Data")

            table.add_row(
                "Client Connection ID",
                str(client_connection.client_connection_id),
            )
            table.add_row("Name", client_connection.name)
            table.add_row("Username", client_connection.username)
            table.add_row("Password", client_connection.password)
            table.add_row("Remote Host", client_connection.remote_host)
            table.add_row("Remote Port", str(client_connection.remote_port))
            table.add_row("Role", role)
            table.add_row(
                "Datetime Connected",
                str(client_connection.datetime_connected.isoformat()),
            )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
