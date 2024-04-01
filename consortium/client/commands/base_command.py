import argparse
from abc import ABC, abstractmethod

from consortium.client.client_session import ClientSession
from consortium.client.objects.command_objects import (
    CommandReturnStatus,
    InterpreterCommand,
)


class BaseCommand(ABC):
    def __init__(self, parser: argparse.ArgumentParser):
        self._parser = parser
        self.name = parser.prog
        self.description = parser.description
        self.summary = f"""description: {parser.description}
{parser.format_usage()}"""
        self.help = self._parser.format_help()

    # When client_session is None, it means that the command is being run in the context
    # whereby the user has not connected to any server at all.
    @abstractmethod
    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None,
        # Avoid circular imports in type hinting by using a string literal.
        interpreter: "BaseInterpreter",
    ) -> CommandReturnStatus: ...
