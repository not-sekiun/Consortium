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
            description="list all info for a specific running listener on the server",
            prog="info_listener",
        )
        parser.add_argument(
            "listener_id",
            help="listener ID of the listener to display info for",
            nargs=1,
            type=int,
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

            response = await remote_server.get_listener_by_id(
                parsed_args.listener_id[0],
            )
            # TODO: Handle errors for non existent ids
            for info, data in response["listener"].items():
                if info == "specific_info":  # only append common info first
                    continue
                # TODO: Find some way to prettify the output to not use snake case as the key
                listener_info_entries.append([info, str(data)])
            for specific_info, specific_data in listener_entry["specific_info"].items():
                listener_info_entries.append([specific_info, str(specific_data)])

            print_status.print_plain(
                f"\n{return_table.main([['Information', 'Data'], ['===========', '===='], *listener_info_entries])}\n",
            )
        except SystemExit:
            pass
        except Exception:
            print_status.print_error(
                f"Invalid listener: {parsed_args.listener_template_id}",
            )
