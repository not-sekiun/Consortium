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


class RenameClientSessionCommand(BaseCommand):
    name = "rename_client_session"
    description = "Rename the current client session or a specific client session."
    epilog = format_argparse_epilog(
        """
        Examples:
          rename_client_session "New name" # Renames the current client session if the client session ID is not specified.
          rename_client_session 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_session_id",
            help="Client session ID of the client session to rename. If not "
            "provided, the name of the current client session is changed.",
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "new_name",
            help="New name to assign to the specified client session.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            if parsed_args.client_session_id is None:
                client_session = command_context.environment["client_session"]
            else:
                try:
                    client_session = (
                        client_sessions_service.get_client_session_by_client_session_id(
                            client_session_id=parsed_args.client_session_id,
                        )
                    )
                except ClientSessionNotFoundError as exc:
                    print_error(str(exc))
                    return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            # Store the previous client session string for the success
            # message to demonstrate the change in name.
            previous_client_session_str = str(client_session)
            client_session.name = parsed_args.new_name[0]
            print_success(
                f"Renamed client session {previous_client_session_str} to: "
                f'"{client_session.name}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
