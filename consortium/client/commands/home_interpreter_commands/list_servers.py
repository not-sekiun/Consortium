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
            description="list all current server connections",
            prog="list_servers",
        )
        super().__init__(parser)

    async def run_command(
        self,
        _remote_server: ClientREST,
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
            _ = self._parser.parse_args(parsed_consortium_command.command_args)
            server_connection_entries = []
            for server_id, server in client_database.get_remote_servers().items():
                server_connection_entries.append(
                    [str(server_id), f"{server.remote_host}:{server.remote_port}"],
                )
            print_status.print_plain(
                f"\n{return_table.main([['Server ID', 'Server Remote Address'], ['=========', '====================='], *server_connection_entries])}\n",
            )
        except SystemExit:
            pass
