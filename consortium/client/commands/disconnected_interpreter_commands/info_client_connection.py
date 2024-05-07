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
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE, print_error

client_connections_service = client_singletons.client_connections_service


class InfoClientConnectionCommand(BaseCommand):
    name = "info_client_connection"
    description = "Display detailed information for a specific client connection."
    epilog = format_argparse_epilog(
        """
        Examples:
            info_client_session 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help=(
                "The client connection ID of the client connection to display detailed "
                "information for."
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
                client_connection = client_connections_service.get_client_connection_by_client_connection_id(
                    parsed_args.client_connection_id[0],
                )
            except ValueError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
            own_user = await client_connection.get_own_user_info()
            server_release = await client_connection.get_server_release()

            table = Table(title="Client Connection Info")
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Client Connection ID",
                str(client_connection.client_connection_id),
            )
            table.add_row("Name", client_connection.name)
            table.add_row("Description", client_connection.description)
            table.add_row("Username", client_connection.username)
            table.add_row("Password", client_connection.password)
            table.add_row("Remote Host", client_connection.remote_host)
            table.add_row("Remote Port", str(client_connection.remote_port))
            table.add_row("Role", own_user["role"])
            table.add_row(
                "Datetime Connected",
                str(client_connection.datetime_connected.isoformat()),
            )
            server_release_table = Table()
            server_release_table.add_column("Information")
            server_release_table.add_column("Data")
            server_release_table.add_row("Version", server_release["version"])
            server_release_table.add_row("Codename", server_release["codename"])
            server_release_table.add_row(
                "Datetime Released",
                server_release["datetime_released"],
            )
            table.add_row("Server Release", server_release_table)
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
