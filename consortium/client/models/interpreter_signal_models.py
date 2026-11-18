from dataclasses import dataclass

from pydantic import JsonValue

from consortium.client.client_session import ClientSession


@dataclass
class InterpreterSignal:
    pass


@dataclass
class ContinueSignal(InterpreterSignal):
    pass


@dataclass
class ExitClientSignal(InterpreterSignal):
    pass


@dataclass
class ExitClientSessionSignal(InterpreterSignal):
    pass


@dataclass
class SwitchHomeInterpreterSignal(InterpreterSignal):
    pass


@dataclass
class SwitchListenersInterpreterSignal(InterpreterSignal):
    pass


@dataclass
class SwitchAgentsInterpreterSignal(InterpreterSignal):
    pass


@dataclass
class SwitchGeneratorsInterpreterSignal(InterpreterSignal):
    pass


@dataclass
class SwitchUseListenerTemplateInterpreterSignal(InterpreterSignal):
    listener_template: dict[str, JsonValue]


@dataclass
class SwitchUseAgentTemplateInterpreterSignal(InterpreterSignal):
    agent_template: dict[str, JsonValue]


@dataclass
class SwitchInteractAgentInterpreterSignal(InterpreterSignal):
    agent: dict[str, JsonValue]


@dataclass
class SwitchClientSessionSignal(InterpreterSignal):
    client_session: ClientSession
