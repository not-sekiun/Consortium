import argparse
from typing import Union

import consortium_old.utils.standard_io.print_status as print_status
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.interpreter_exit_signal import (
    InterpreterExitSignal,
)
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class HomeCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="disconnect the current server connection or a specific server connection",
            prog="disconnect",
        )
        parser.add_argument(
            "server_id",
            help="server ID of the server connection to disconnect. if no ID is passed in the current server connection is disconnected",
            nargs="?",
            type=int,
            default=None,
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
    ) -> Union[None, InterpreterExitSignal]:
        try:
            parsed_args = self._parser.parse_args(
                parsed_consortium_command.command_args,
            )
            disconnected_current_server_connection = False
            if parsed_args.server_id:
                if parsed_args.server_id == remote_server.server_id:
                    disconnected_current_server_connection = True
                if parsed_args.server_id in client_database.get_remote_servers():
                    target_remote_server = client_database.get_remote_servers()[
                        parsed_args.server_id
                    ]
                else:
                    print_status.print_error(f"Invalid server: {parsed_args.server_id}")
                    return
            else:
                target_remote_server = remote_server
                disconnected_current_server_connection = True

            await target_remote_server.disconnect_server()
            print_status.print_success(
                f"Disconnected from server: {target_remote_server.server_id}",
            )
            del client_database.get_remote_servers()[target_remote_server.server_id]

            if not client_database.get_remote_servers():
                print_status.print_error("No valid servers present")
                print_status.print_indented(
                    "Automatically switching to disconnected interpreter...",
                    print_func=print_status.print_info,
                )
                print_status.print_indented(
                    'Your commands are limited until you connect back to a server with the "connect" command',
                    print_func=print_status.print_info,
                )
            elif (
                disconnected_current_server_connection
                and client_database.get_remote_servers()
            ):
                next_valid_connection_id = list(
                    client_database.get_remote_servers().keys(),
                )[0]
                print_status.print_info(
                    "Automatically switching to the next valid connection...",
                )
                return InterpreterExitSignal(
                    switch_server=True,
                    new_server_id=next_valid_connection_id,
                )
        except SystemExit:
            pass
