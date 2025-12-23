from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.commands.home_interpreter_commands.info_client_session import (
    InfoClientSessionCommand as HomeInterpreterClientSessionCommand,
)
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionNotFoundError,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error

client_sessions_service = client_singletons.client_sessions_service


class InfoClientSessionCommand(HomeInterpreterClientSessionCommand):
    description = "Display detailed information for a specific client session."
    epilog = format_argparse_epilog(
        """
        Examples:
          info_client_session 123e4567-e89b-12d3-a456-42661417400
        """,
    )

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

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            try:
                client_session = (
                    client_sessions_service.get_client_session_by_client_session_id(
                        parsed_args.client_session_id[0],
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
