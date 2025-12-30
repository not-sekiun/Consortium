from argparse import ArgumentParser
from typing import TYPE_CHECKING

from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.client_rest_api import RestAPI
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
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_role_str_with_color,
)
from consortium.client.utils.printer_utils import console, print_error

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession

client_sessions_service = client_singletons.client_sessions_service


class ClientSessionInfoCommand(BaseCommand):
    name = "info"
    description = (
        "Display information for the current client session, or for a "
        "specific client session by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info -p  # Displays password
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "ID of the client session to display information for (defaults to the "
                "current client session if not provided)."
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
        rest_api: RestAPI,
        show_password: bool,
    ) -> None:
        own_user_info = await rest_api.get_own_user_info()
        server_release = await rest_api.get_server_release()

        table = Table(title="Client Session Information", highlight=True)
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
        table.add_row("Role", format_role_str_with_color(role=own_user_info["role"]))
        table.add_row("Connected", str(client_session.connected))
        table.add_row(
            "Datetime Connected",
            format_datetime_as_human_readable_str(
                datetime_str=client_session.datetime_connected,
                include_elapsed_time=True,
            ),
        )
        table.add_row(
            "Server Release",
            f"v{server_release['version']} ({server_release['codename']}) released "
            f"{format_datetime_as_human_readable_str(datetime_str=server_release['datetime_released'])}",
        )
        console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.client_session_id is None:
                await self._display_client_session_info(
                    client_session=context.client_session,
                    rest_api=context.client_session.rest_api,
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
                        rest_api=client_session.rest_api,
                        show_password=parsed_args.password,
                    )
                except ClientSessionNotFoundError as exc:
                    print_error(str(exc))
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
