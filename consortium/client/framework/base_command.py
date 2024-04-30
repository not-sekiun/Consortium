from abc import ABC, abstractmethod
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import dataclass


@dataclass
class CommandContext:
    command: str
    arguments: list[str]
    original_string: str
    environment: dict


@dataclass
class ReturnStatusType:
    CONTINUE = "CONTINUE"
    EXIT = "EXIT"


@dataclass
class ReturnStatus:
    type: ReturnStatusType
    data: dict | None = None


class BaseCommand(ABC):
    name: str
    description: str = ""
    epilog: str = ""

    def __init__(self, environment: dict | None = None) -> None:
        if environment is None:
            environment = {}

        self.environment = environment
        self.parser = ArgumentParser(
            prog=self.name,
            description=self.description,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.epilog,
        )
        self.summary = (
            f"description: {self.parser.description}\n{self.parser.format_usage()}"
        )
        self.configure_parser(self.parser)

    @abstractmethod
    def configure_parser(self, parser: ArgumentParser) -> None: ...

    @abstractmethod
    async def run_command(self, command_context: CommandContext) -> ReturnStatus: ...
