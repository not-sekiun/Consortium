from abc import ABC, abstractmethod
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from typing import Any

from pydantic import BaseModel, ConfigDict

from consortium.client.client_session import ClientSession
from consortium.client.models.return_status_models import ReturnStatus


class Context(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    command: str
    arguments: list[str]
    raw_input: str
    client_session: ClientSession | None
    interpreter_context: Any
    # FIXME: Deprecate environment in favor of interpreter_context + remove client session related data from environment
    environment: dict


class BaseCommand(ABC):
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
    async def run(self, context: Context) -> ReturnStatus: ...
