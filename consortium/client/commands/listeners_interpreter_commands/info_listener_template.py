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
            description="list all info for a specific listener template on the server",
            prog="info_listener_template",
        )
        parser.add_argument(
            "listener_template_id",
            help="listener template ID of the listener template to display info for",
            type=int,
            nargs=1,
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        _client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        _interpreter: "ListenersInterpreter",
    ) -> None:
        try:
            parsed_args = self._parser.parse_args(
                parsed_consortium_command.command_args,
            )

            response = await remote_server.get_listener_template_by_id(
                parsed_args.listener_template_id[0],
            )
            found_listener_template_entry = False
            listener_template_info_entries = []
            for listener_template_entry in response["listener_templates"]:
                if (
                    listener_template_entry["listener_template_id"]
                    == parsed_args.listener_template_id[0]
                ):
                    for info, data in listener_template_entry.items():
                        # TODO: Find some way to prettify the output to not use snake case as the key, this is only being done here for consistency with other info_ commands
                        listener_template_info_entries.append([info, str(data)])
                    found_listener_template_entry = True

            if not found_listener_template_entry:
                print_status.print_error(
                    f"Invalid listener template: {parsed_args.listener_template_id[0]}",
                )
                return

            print_status.print_plain(
                f"\n{return_table.main([['Information', 'Data'], ['===========', '===='], *listener_template_info_entries])}\n",
            )
        except SystemExit:
            pass
