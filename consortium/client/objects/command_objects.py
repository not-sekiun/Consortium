from dataclasses import dataclass
from enum import StrEnum

from consortium.client.objects.interpreter_objects import InterpreterType


class CommandReturnState(StrEnum):
    CONTINUE = "CONTINUE"
    EXIT_PROGRAM = "EXIT_PROGRAM"
    SWITCH_INTERPRETER = "SWITCH_INTERPRETER"
    SWITCH_CLIENT_SESSION = "SWITCH_CLIENT_SESSION"
    EXIT_CLIENT_SESSION = "EXIT_CLIENT_SESSION"


class ReturnStatus:
    def __init__(self, state: CommandReturnState):
        self.state = state


class ContinueReturnStatus(ReturnStatus):
    def __init__(self):
        super().__init__(CommandReturnState.CONTINUE)


class ExitProgramReturnStatus(ReturnStatus):
    def __init__(self):
        super().__init__(CommandReturnState.EXIT_PROGRAM)


class SwitchInterpreterReturnStatus(ReturnStatus):
    def __init__(self, interpreter_type: InterpreterType):
        super().__init__(CommandReturnState.SWITCH_INTERPRETER)
        self.interpreter_type = interpreter_type


class ExitClientSessionReturnStatus(ReturnStatus):
    def __init__(self):
        super().__init__(CommandReturnState.EXIT_CLIENT_SESSION)


class SwitchClientSessionReturnStatus(ReturnStatus):
    def __init__(self, client_session_id: str | None):
        super().__init__(CommandReturnState.SWITCH_CLIENT_SESSION)
        # client_session_id being None implies that we simply exit the current client
        # session rather than automatically switching.
        self.client_session_id = client_session_id


@dataclass
class InterpreterCommand:
    command: str
    arguments: list[str]
    original_string: str
