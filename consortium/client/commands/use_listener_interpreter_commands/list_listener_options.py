import argparse

import consortium_old.utils.standard_io.print_status as print_status
import consortium_old.utils.standard_io.return_table as return_table
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class UseListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="list all options for a specific listener template on the server",
            prog="list_listener_options",
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        _client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        interpreter: "UseListenerInterpreter",
    ) -> None:
        try:
            _ = self._parser.parse_args(parsed_consortium_command.command_args)

            listener_template_options_entries = []
            for option, data in interpreter.listener_template_options.items():
                listener_template_options_entries.append(
                    [
                        option,
                        str(data["value"]),
                        data["type"],
                        str(data["required"]),
                        data["description"],
                    ],
                )
            print_status.print_plain(
                f"\n{return_table.main([['Option', 'Value', 'Type', 'Required', 'Description'], ['======', '=====', '====', '========', '==========='], *listener_template_options_entries])}\n",
            )
        except SystemExit:
            pass
