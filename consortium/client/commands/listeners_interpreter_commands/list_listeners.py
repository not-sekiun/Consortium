import argparse

import consortium_old.utils.standard_io.print_status as print_status
import consortium_old.utils.standard_io.return_table as return_table
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class ListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="list all running listeners on the server",
            prog="list_listeners",
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        _interpreter: "ListenersInterpreter",
    ) -> None:
        try:
            _ = self._parser.parse_args(parsed_consortium_command.command_args)
            listener_entries = []
            response = await remote_server.get_listeners()
            for listener_entry in response["listeners"]:
                listener_entries.append(
                    [
                        str(listener_entry["listener_id"]),
                        listener_entry["name"],
                        listener_entry["listener_type"],
                        listener_entry["endpoint"],
                    ],
                )
            print_status.print_plain(
                f"\n{return_table.main([['Listener ID', 'Listener Name', 'Listener Type', 'Listener endpoint'], ['===========', '=============', '=============', '================='], *listener_entries])}\n",
            )
        except SystemExit:
            pass
