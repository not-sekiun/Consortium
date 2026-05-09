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
    client_session: ClientSession | None
    interpreter_context: dict[str, Any]
