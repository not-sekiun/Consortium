import argparse
from typing import Union

import consortium_old.utils.standard_io.print_status as print_status
import consortium_old.utils.standard_io.return_table as return_table
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class HomeCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="list all info for the current server connection or for a specific server connection",
            prog="info_server",
        )
        parser.add_argument(
            "server_id",
            help="server ID of the server connection to display info for. if not passed in, info for the current server connection is displayed",
            nargs="?",
            type=int,
            default=None,
        )
        parser.add_argument(
            "-p",
            "--password",
            help="Allow this command to display the password used to connect to the server",
            action="store_true",
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        _interpreter: Union[
            "HomeInterpreter",
            "DisconnectedInterpreter",
            "ListenersInterpreter",
            "GeneratorInterpreter",
            "AgentsInterpreter",
        ],  # TODO: Gradually fill this out with more interpreters
    ) -> None:
        try:
            parsed_args = self._parser.parse_args(
                parsed_consortium_command.command_args,
            )

            if parsed_args.password:
                displayed_password = remote_server.password
            else:
                displayed_password = ""

            if parsed_args.server_id:
                if parsed_args.server_id in client_database.get_remote_servers():
                    displayed_remote_server = client_database.get_remote_servers()[
                        parsed_args.server_id
                    ]
                else:
                    print_status.print_error(f"Invalid server: {parsed_args.server_id}")
                    return
            else:
                displayed_remote_server = remote_server

            response = await displayed_remote_server.get_basic_server_info()
            server_connection_info_entries = [
                ["remote_host", remote_server.remote_host],
                ["remote_port", str(remote_server.remote_port)],
                ["username", remote_server.username],
                ["password", displayed_password],
                ["server_version", remote_server.version],
                ["account_type", remote_server.account_type],
                ["server_id", str(remote_server.server_id)],
                ["datetime_connected", remote_server.datetime_connected],
                ["number_of_listeners", str(response["number_of_listeners"])],
                ["number_of_operators", str(response["number_of_operators"])],
                ["number_of_admins", str(response["number_of_admins"])],
                ["number_of_agents", str(response["number_of_agents"])],
            ]  # TODO: Find some way to prettify the output to not use snake case as the key, this is only being done here for consistency with other info_ commands
            if not parsed_args.password:
                print_status.print_info(
                    'Password field is hidden by default, override with "-p"',
                )
            print_status.print_plain(
                f"\n{return_table.main([['Information', 'Data'], ['===========', '===='], *server_connection_info_entries])}\n",
            )
        except SystemExit:
            pass
