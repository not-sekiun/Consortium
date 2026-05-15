from abc import ABC, abstractmethod
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from consortium.client.models.context_models import (
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_signal_models import InterpreterSignal


# BaseCommand is parameterized by the type of context it receives. It defaults to
# ConnectedContext since this is the case for most Commands, but it can be set to
# DisconnectedContext for Commands that should be available in the disconnected
# interpreter.
class BaseCommand[T: (ConnectedContext, DisconnectedContext) = ConnectedContext](ABC):
    name: str
    description: str = ""
    epilog: str = ""
    group: str = ""

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
        self.configure_parser(self.parser)

    # When implementations of this BaseCommand abstract base class are created the
    # summary is automatically created as a class attribute to reflect the
    # implementation's parser.
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.summary = f"description: {cls.description}\n{cls().parser.format_usage()}"

    def configure_parser(self, parser: ArgumentParser) -> None:
        return None

    @abstractmethod
    async def run(self, context: T) -> InterpreterSignal: ...
