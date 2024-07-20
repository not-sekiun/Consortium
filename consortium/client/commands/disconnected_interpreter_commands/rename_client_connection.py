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


class RenameClientConnectionCommand(BaseCommand):
    name = "rename_client_connection"
    description = "Rename a specific client connection."
    epilog = format_argparse_epilog(
        """
        Examples:
            rename_client_connection 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "client_connection_id",
            help="Client connection ID of the client connection to rename.",
            nargs=1,
            default=None,
        )
        parser.add_argument(
            "new_name",
            help="New name to assign to the specified client connection.",
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
                    f"Invalid client connection ID: {parsed_args.client_connection_id[0]}",
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            previous_client_connection_str = str(client_connection)
            client_connection.name = parsed_args.new_name[0]
            print_success(
                f"Renamed client connection {previous_client_connection_str} to: "
                f'"{client_connection.name}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
