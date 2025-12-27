from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import CONSOLE

client_sessions_service = client_singletons.client_sessions_service


class ClientSessionListCommand(BaseCommand):
    name = "list"
    description = "List all client sessions along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Client Session Management Commands"

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            all_client_sessions = client_sessions_service.get_all_client_sessions()

            table = Table(title="Client Sessions", highlight=True)
            table.add_column("Client Session ID")
            table.add_column("Name")
            table.add_column("Username")
            table.add_column("Remote Host")
            table.add_column("Remote Port")
            for client_session in all_client_sessions:
                table.add_row(
                    str(client_session.client_session_id),
                    str(client_session.name),
                    str(client_session.username),
                    str(client_session.remote_host),
                    str(client_session.remote_port),
                )
            CONSOLE.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
