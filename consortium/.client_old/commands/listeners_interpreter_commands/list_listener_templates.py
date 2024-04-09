import argparse

from rich.console import Console
from rich.table import Table

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)

client_sessions_service = client_singletons.client_sessions_service


class ListListenerTemplatesCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="List all listener templates.",
            prog="list_listener_templates",
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            all_listener_templates = await client_session.get_all_listener_templates()

            table = Table(title="Listener Templates")
            table.add_column("Listener Template ID")
            table.add_column("Name")

            for listener_template in all_listener_templates:
                table.add_row(
                    listener_template["listener_template_id"],
                    listener_template["name"],
                )

            Console().print(table)
        except SystemExit:
            pass

        return ContinueReturnStatus()
