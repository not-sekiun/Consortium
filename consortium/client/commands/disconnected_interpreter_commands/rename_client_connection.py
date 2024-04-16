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
from consortium.client.utils.printer_utils import print_error, print_success
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class RenameClientConnectionCommand(BaseCommand):
    name = "rename_client_connection"
    description = "Rename a specific client connection by its client connection ID."
    epilog = argparse_epilog_formatter(
        """
        Example:
            rename_client_connection 123e4567-e89b-12d3-a456-42661417400 "Client Connection Name"  # Rename a client connection with client connection ID 123e4567-e89b-12d3-a456-42661417400 to "Client Connection Name"
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
            "name",
            help="Name to rename the client connection to.",
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

            print_success(
                f'Renamed client connection {client_connection} to: "{parsed_args.name[0]}"',
            )
            client_connection.name = parsed_args.name[0]
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
