import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info, print_success

client_sessions_service = client_singletons.client_sessions_service


class ExitCommand(BaseCommand):
    name = "exit"
    description = "Exit the Consortium client"
    epilog = format_argparse_epilog(
        """
        Examples:
          exit
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

            print_info("Disconnecting all client sessions...")
            for client_session in client_sessions_service.get_all_client_sessions():
                if not client_session.connected:
                    continue

                try:
                    await client_session.disconnect()
                    print_success(
                        f"Disconnected client session {client_session}",
                    )
                except Exception as exc:
                    print_error(
                        f"Error disconnecting client session {client_session}: {exc}",
                    )

            print_info("Exiting...")
            return ReturnStatus(
                type=ClientReturnStatusType.EXIT,
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
