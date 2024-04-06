import argparse
from abc import ABC, abstractmethod
from typing import Optional

from consortium.client.client_session import ClientSession
from consortium.client.objects.command_objects import InterpreterCommand, ReturnStatus


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
        client_session: ClientSession | None = None,
        # Avoid circular imports in type hinting by using a string literal. We use
        # Optional instead of "BaseInterpreter" | None because the | operator is not
        # supported for string forward references in type hinting 🤡. For the
        # instantiated commands we can use the type hint without the forward reference
        # because those commands are not imported by the BaseInterpreter (thus
        # preventing circularity).
        interpreter: Optional["BaseInterpreter"] = None,
    ) -> ReturnStatus: ...
