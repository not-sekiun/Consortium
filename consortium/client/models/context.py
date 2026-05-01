from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel, ConfigDict

from consortium.client.client_session import ClientSession


class InterpreterAction(StrEnum):
    CONTINUE = auto()
    EXIT = auto()
    SWITCH_INTERPRETER = auto()
    SWITCH_CLIENT_SESSION = auto()


class InterpreterContext(BaseModel):
    action: InterpreterAction


class Context(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # Command context, context passed to the command function when executing a command
    # from the interpreter parser.
    command: str
    arguments: list[str]
    raw_input: str

    # Session context, context related to the client session, such as the currently
    # connected client session and any aliases for client sessions. Aliases and resource
    # commands are session in
    client_session: ClientSession | None
    aliases: dict[str, str]
    resource_commands: list[str]

    # Interpreter context
    interpreter_context: dict[str, Any]
