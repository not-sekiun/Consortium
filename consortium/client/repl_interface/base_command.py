from abc import ABC, abstractmethod
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from typing import TYPE_CHECKING

from consortium.client.models.interpreter_signal_models import InterpreterSignal

if TYPE_CHECKING:
    from consortium.client.models.context_models import (
        AnyContext,
        ConnectedContext,
        DisconnectedContext,
    )


class BaseCommand[TContext: (ConnectedContext, DisconnectedContext, AnyContext)](ABC):
    name: str
    description: str = ""
    epilog: str = ""
    group: str = ""

    def __init__(self):
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
    async def run(self, context: TContext) -> InterpreterSignal: ...
