from argparse import ArgumentParser

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
from consortium.client.utils.printer_utils import print_error, print_success

client_connections_service = client_singletons.client_connections_service


class RedescribeClientConnectionCommand(BaseCommand):
    name = "redescribe_client_connection"
    description = "Change the description of a specific client connection."
    epilog = format_argparse_epilog(
        """
        Examples:
          redescribe_client_connection 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help=(
                "Client connection ID of the client connection to change the "
                "description of."
            ),
            nargs=1,
        )
        parser.add_argument(
            "new_description",
            help="New description to assign to the specified client connection.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            try:
                client_connection = client_connections_service.get_client_connection_by_client_connection_id(
                    client_connection_id=parsed_args.client_connection_id[0],
                )
            except ValueError:
                print_error(
                    f"Invalid client connection ID "
                    f"'{parsed_args.client_connection_id}'",
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            client_connection.description = parsed_args.new_description[0]
            print_success(
                f"Client connection {client_connection} description updated to: "
                f'"{client_connection.description}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
