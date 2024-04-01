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
            description="interact with a specific server connections",
            prog="interact_server",
        )
        parser.add_argument(
            "server_id",
            help="server ID of the server connection to interact with",
            nargs=1,
            type=int,
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
            if parsed_args.server_id[0] == remote_server.server_id:
                print_status.print_error("Already interacting with that server")
            elif parsed_args.server_id[0] in client_database.get_remote_servers():
                print_status.print_success(
                    f"Interacting with server: {parsed_args.server_id[0]}...",
                )
                # TODO: Maybe at some point make connection related commands global?
                # print_status.indent(
                #     "Automatically switching to home interpreter...",
                #     print_func=print_status.info,
                # )
                return InterpreterExitSignal(
                    switch_server=True,
                    new_server_id=parsed_args.server_id[0],
                )
            else:
                print_status.print_error(f"Invalid server: {parsed_args.server_id[0]}")
        except SystemExit:
            pass
