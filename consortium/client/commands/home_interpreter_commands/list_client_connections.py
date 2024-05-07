import argparse

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
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE

client_connections_service = client_singletons.client_connections_service


class ListClientConnectionsCommand(BaseCommand):
    name = "list_client_connections"
    description = (
        "List basic information for all current client connections to a Consortium "
        "server."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            list_client_connections
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_client_connections = (
                client_connections_service.get_all_client_connections()
            )

            table = Table(title="Client Connections")
            table.add_column("Client Connection ID")
            table.add_column("Name")
            table.add_column("Remote Host")
            table.add_column("Remote Port")
            for client_connection in all_client_connections:
                table.add_row(
                    str(client_connection.client_connection_id),
                    client_connection.name,
                    client_connection.remote_host,
                    str(client_connection.remote_port),
                )
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
