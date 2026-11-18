from argparse import Namespace
from dataclasses import dataclass

from consortium.client.client_session import ClientSession
from consortium.client.models.interpreter_context_models import BaseInterpreterContext


@dataclass
class _Context:
    command: str
    arguments: list[str]
    parsed_args: Namespace
    raw_input: str
    interpreter_context: BaseInterpreterContext


@dataclass
class ConnectedContext(_Context):
    client_session: ClientSession


@dataclass
class DisconnectedContext(_Context): ...


type AnyContext = ConnectedContext | DisconnectedContext
