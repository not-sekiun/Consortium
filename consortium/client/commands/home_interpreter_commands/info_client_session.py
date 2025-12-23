from argparse import ArgumentParser
from typing import TYPE_CHECKING

from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
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

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

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
          info_client_session -p  # Does not hide password
          info_client_session 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

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
        parser.add_argument(
            "-p",
            "--password",
            help="Display the password of the client session.",
            action="store_true",
            default=False,
        )

    @staticmethod
    async def _display_client_session_info(
        client_session: ClientSession,
        client_rest_api_connection: ClientRESTAPIConnection,
        show_password: bool,
    ) -> None:
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
        table.add_row(
            "Password", client_session.password if show_password else "********"
        )
        table.add_row("Remote Host", client_session.remote_host)
        table.add_row("Remote Port", str(client_session.remote_port))
        table.add_row("Role", own_user_info["role"])
        table.add_row("Connected", str(client_session.connected))
        table.add_row(
            "Datetime Connected",
            str(client_session.datetime_connected.isoformat()),
        )
        table.add_row(
            "Server Release",
            f"v{server_release['version']} ({server_release['codename']}) released "
            f"{server_release['datetime_released']}",
        )
        CONSOLE.print(table)

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            if parsed_args.client_session_id is None:
                await self._display_client_session_info(
                    client_session=command_context.environment["client_session"],
                    client_rest_api_connection=command_context.environment[
                        "client_rest_api_connection"
                    ],
                    show_password=parsed_args.password,
                )
            else:
                try:
                    client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            client_session_id=parsed_args.client_session_id,
                        )
                    )
                    await self._display_client_session_info(
                        client_session=client_session,
                        client_rest_api_connection=client_session.client_rest_api_connection,
                        show_password=parsed_args.password,
                    )
                except ClientSessionNotFoundError as exc:
                    print_error(str(exc))
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
