from rich.table import Table

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
from consortium.client.utils.printer_utils import CONSOLE

client_sessions_service = client_singletons.client_sessions_service


class ListClientSessionsCommand(BaseCommand):
    name = "list_client_sessions"
    description = (
        "List basic information for all current client sessions to a Consortium server."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_client_sessions
        """,
    )
    group = "Client Session Management Commands"

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_client_sessions = client_sessions_service.get_all_client_sessions()

            table = Table(title="Client Sessions")
            table.add_column("Client Session ID")
            table.add_column("Name")
            table.add_column("Username")
            table.add_column("Remote Host")
            table.add_column("Remote Port")
            for client_session in all_client_sessions:
                table.add_row(
                    str(client_session.client_session_id),
                    client_session.name,
                    client_session.username,
                    client_session.remote_host,
                    str(client_session.remote_port),
                )
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
