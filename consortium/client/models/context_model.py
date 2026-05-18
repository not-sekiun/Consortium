from typing import Any

from pydantic import BaseModel, ConfigDict

from consortium.client.client_session import ClientSession


class Context(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    command: str
    arguments: list[str]
    raw_input: str
    interpreter_context: dict[str, Any]
    client_session: ClientSession | None = None
