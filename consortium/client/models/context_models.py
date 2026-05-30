from pydantic import BaseModel, ConfigDict

from consortium.client.client_session import ClientSession
from consortium.client.models.interpreter_context_models import BaseInterpreterContext


class _Context(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    command: str
    arguments: list[str]
    raw_input: str
    interpreter_context: BaseInterpreterContext


class ConnectedContext(_Context):
    client_session: ClientSession


class DisconnectedContext(_Context):
    client_session: None


type AnyContext = ConnectedContext | DisconnectedContext
