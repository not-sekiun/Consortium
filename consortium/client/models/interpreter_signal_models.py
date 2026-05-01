from pydantic import BaseModel, JsonValue

from consortium.client.client_session import ClientSession


class InterpreterSignal(BaseModel):
    pass


class ContinueSignal(InterpreterSignal):
    pass


class ExitClientSignal(InterpreterSignal):
    pass


class ExitClientSessionSignal(InterpreterSignal):
    pass


class SwitchHomeInterpreterSignal(InterpreterSignal):
    pass


class SwitchListenersInterpreterSignal(InterpreterSignal):
    pass


class SwitchAgentsInterpreterSignal(InterpreterSignal):
    pass


class SwitchGeneratorsInterpreterSignal(InterpreterSignal):
    pass


class SwitchUseListenerTemplateInterpreterSignal(InterpreterSignal):
    listener_template: dict[str, JsonValue]


class SwitchUseAgentTemplateInterpreterSignal(InterpreterSignal):
    agent_template: dict[str, JsonValue]


class SwitchInteractAgentInterpreterSignal(InterpreterSignal):
    agent: dict[str, JsonValue]


class SwitchClientSessionSignal(InterpreterSignal):
    class Config:
        arbitrary_types_allowed = True

    client_session: ClientSession
