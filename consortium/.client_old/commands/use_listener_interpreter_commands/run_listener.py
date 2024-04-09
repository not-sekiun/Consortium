import argparse

from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class UseListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="run a specific listener associated with its listener template on the server",
            prog="run_listener",
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
        except SystemExit:
            pass
