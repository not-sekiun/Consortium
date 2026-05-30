import inspect
from abc import ABC, abstractmethod
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from consortium.client.models.context_models import (
    AnyContext,
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_signal_models import InterpreterSignal


class BaseCommand[
    TContext: (ConnectedContext, DisconnectedContext, AnyContext) = AnyContext
](ABC):
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
        # Guard clause to prevent the firing of the init subclass logic for
        # `BaseConnectedCommand` and `BaseDisconnectedCommand`
        if ABC in cls.__bases__ or inspect.isabstract(cls):
            return
        cls.summary = f"description: {cls.description}\n{cls().parser.format_usage()}"

    def configure_parser(self, parser: ArgumentParser) -> None:
        return None

    @abstractmethod
    async def run(self, context: TContext) -> InterpreterSignal: ...


class BaseConnectedCommand(BaseCommand[ConnectedContext], ABC):
    @abstractmethod
    async def run(self, context: ConnectedContext) -> InterpreterSignal: ...


class BaseDisconnectedCommand(BaseCommand[DisconnectedContext]):
    @abstractmethod
    async def run(self, context: DisconnectedContext) -> InterpreterSignal: ...
