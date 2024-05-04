import argparse

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
from consortium.client.utils.printer_utils import print_error, print_info, print_success

client_connections_service = client_singletons.client_connections_service


class ExitCommand(BaseCommand):
    name = "exit"
    description = "Exit the Consortium client."
    epilog = format_argparse_epilog(
        """
        Examples:
            exit  # Exit the Consortium client.
        """,
    )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)

            print_info("Disconnecting all client connections...")

            for (
                client_connection
            ) in client_connections_service.get_all_client_connections():
                try:
                    await client_connection.logout()
                    print_success(
                        f"Disconnected client connection: {client_connection}",
                    )
                except Exception as exc:
                    print_error(f"Error disconnecting client connection: {exc}")

            print_info("Exiting...")
            return ReturnStatus(
                type=ClientReturnStatusType.EXIT,
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
