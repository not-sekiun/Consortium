from typing import Any

from pydantic import BaseModel, ConfigDict

from consortium.client.client_session import ClientSession


class _Context(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    command: str
    arguments: list[str]
    raw_input: str
    interpreter_context: dict[str, Any]


class ConnectedContext(_Context):
    client_session: ClientSession


class DisconnectedContext(_Context):
    pass


# Create a lazily evaluated type alias for commands that accept either type
type AnyContext = ConnectedContext | DisconnectedContext
