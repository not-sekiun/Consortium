from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class ListListenersCommand(BaseCommand):
    name = "list_listeners"
    description = "List all listeners."
    epilog = argparse_epilog_formatter(
        """
        Example:
            list_listeners  # List all listeners
        """,
    )

    def configure_parser(self, parser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_listeners = await command_context.environment[
                "client_connection"
            ].get_all_listeners()

            table = Table(title="Listeners")

            table.add_column("Listener ID")
            table.add_column("Name")
            table.add_column("Endpoint")
            table.add_column("Status")

            for listener in all_listeners:
                listener_status_string = listener["status"]["state"]
                if listener_status_string == "RUNNING":
                    listener_status_string = f"[bold green]{listener_status_string}"
                elif listener_status_string == "ERRORED":
                    listener_status_string = f"[bold red]{listener_status_string}"

                table.add_row(
                    listener["listener_id"],
                    listener["name"],
                    listener["endpoint"],
                    listener_status_string,
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
