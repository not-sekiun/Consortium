from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.home_interpreter_commands.client_session_info import (
    ClientSessionInfoCommand as HomeInterpreterClientSessionInfoCommand,
)
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error

client_sessions_service = client_singletons.client_sessions_service


class ClientSessionInfoCommand(HomeInterpreterClientSessionInfoCommand):
    name = "info"
    description = "Display information for a client session by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "The client session ID of the client session to display detailed "
                "information for."
            ),
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "-p",
            "--password",
            help="Display the password of the client session.",
            action="store_true",
            default=False,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            try:
                client_session = (
                    client_sessions_service.get_client_session_by_client_session_id(
                        parsed_args.client_session_id[0],
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
