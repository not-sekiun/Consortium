from argparse import ArgumentParser

from rich.table import Table

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
from consortium.client.utils.printer_utils import CONSOLE, print_error

client_sessions_service = client_singletons.client_sessions_service


class InfoClientSessionCommand(BaseCommand):
    name = "info_client_session"
    description = (
        "Display detailed information for the current client session or for a "
        "specific client session."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info_client_session  # Displays detailed information for the current client session if the client session ID is not specified.
          info_client_session 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "The client session ID of the client session to display detailed "
                "information for. If not provided, detailed information for the "
                "current client session is displayed."
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

            if parsed_args.client_session_id is None:
                client_session = command_context.environment["client_session"]
                client_rest_api_connection = command_context.environment[
                    "client_rest_api_connection"
                ]
            else:
                try:
                    client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            parsed_args.client_session_id,
                        )
                    )
                    client_rest_api_connection = (
                        client_session.client_rest_api_connection
                    )
                except ClientSessionNotFoundError as exc:
                    print_error(str(exc))
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            own_user_info = await client_rest_api_connection.get_own_user_info()
            server_release = await client_rest_api_connection.get_server_release()

            table = Table(title="Client Session Information")
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Client Session ID",
                str(client_session.client_session_id),
            )
            table.add_row("Name", client_session.name)
            table.add_row("Description", client_session.description)
            table.add_row("Username", client_session.username)
            table.add_row("Password", client_session.password)
            table.add_row("Remote Host", client_session.remote_host)
            table.add_row("Remote Port", str(client_session.remote_port))
            table.add_row("Role", own_user_info["role"])
            table.add_row("Connected", str(client_session.connected))
            table.add_row(
                "Datetime Connected",
                str(client_session.datetime_connected.isoformat()),
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
