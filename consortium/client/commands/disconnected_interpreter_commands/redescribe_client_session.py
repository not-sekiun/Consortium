from argparse import ArgumentParser

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
from consortium.client.utils.printer_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class RedescribeClientSessionCommand(BaseCommand):
    name = "redescribe_client_session"
    description = "Change the description of a specific client session."
    epilog = format_argparse_epilog(
        """
        Examples:
          redescribe_client_session 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Client Session Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help=(
                "Client session ID of the client session to change the description of."
            ),
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "new_description",
            help="New description to assign to the specified client session.",
            nargs=1,
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
                        client_session_id=parsed_args.client_session_id[0],
                    )
                )
            except ClientSessionNotFoundError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            client_session.description = parsed_args.new_description[0]
            print_success(
                f"Client session {client_session} description updated to: "
                f'"{client_session.description}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
