from dataclasses import dataclass
from enum import StrEnum

from consortium.client.objects.interpreter_objects import InterpreterType


class CommandReturnState(StrEnum):
    CONTINUE = "CONTINUE"
    EXIT_PROGRAM = "EXIT_PROGRAM"
    SWITCH_INTERPRETER = "SWITCH_INTERPRETER"


class CommandReturnStatus:
    def __init__(self, state: CommandReturnState):
        self.state = state


class ContinueReturnStatus(CommandReturnStatus):
    def __init__(self):
        super().__init__(CommandReturnState.CONTINUE)


class ExitProgramReturnStatus(CommandReturnStatus):
    def __init__(self):
        super().__init__(CommandReturnState.EXIT_PROGRAM)


class SwitchInterpreterReturnStatus(CommandReturnStatus):
    def __init__(self, interpreter_type: InterpreterType):
        super().__init__(CommandReturnState.SWITCH_INTERPRETER)
        self.interpreter_type = interpreter_type


@dataclass
class InterpreterCommand:
    command: str
    arguments: list[str]
    original_string: str
