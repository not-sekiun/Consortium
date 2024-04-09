from enum import StrEnum
from typing import Any

from pydantic import BaseModel, field_validator


class ReturnStatusType(StrEnum):
    CONTINUE = "CONTINUE"
    EXIT_PROGRAM = "EXIT_PROGRAM"
    EXIT_CLIENT_SESSION = "EXIT_CLIENT_SESSION"
    SWITCH_CLIENT_SESSION = "SWITCH_CLIENT_SESSION"
    SWITCH_INTERPRETER = "SWITCH_INTERPRETER"


class InterpreterType(StrEnum):
    HOME = "HOME"
    LISTENERS = "LISTENERS"
    AGENTS = "AGENTS"
    GENERATORS = "GENERATORS"
    CREATE_LISTENER = "CREATE_LISTENER"
    CREATE_GENERATOR = "CREATE_GENERATOR"
    DISCONNECTED = "DISCONNECTED"


class ReturnStatus(BaseModel):
    return_status_type: ReturnStatusType
    data: Any = None


class SwitchInterpreterReturnStatus(ReturnStatus):
    return_status_type: ReturnStatusType = ReturnStatusType.SWITCH_INTERPRETER
    interpreter_type: InterpreterType

    @field_validator("return_status_type")
    @classmethod
    def check_return_status_type(cls, return_status_type, _values) -> ReturnStatusType:
        if return_status_type != ReturnStatusType.SWITCH_INTERPRETER:
            raise ValueError(
                f"return_status_type must be {ReturnStatusType.SWITCH_INTERPRETER}",
            )
        return return_status_type


class SwitchToCreateListenerInterpreterReturnStatus(SwitchInterpreterReturnStatus):
    interpreter_type: InterpreterType = InterpreterType.CREATE_LISTENER
    listener_template_id: str

    @field_validator("interpreter_type")
    @classmethod
    def check_interpreter_type(cls, interpreter_type, _values) -> InterpreterType:
        if interpreter_type != InterpreterType.CREATE_LISTENER:
            raise ValueError(
                f"interpreter_type must be {InterpreterType.CREATE_LISTENER}",
            )
        return interpreter_type


class SwitchToCreateGeneratorInterpreterReturnStatus(SwitchInterpreterReturnStatus):
    interpreter_type: InterpreterType = InterpreterType.CREATE_GENERATOR
    agent_generator_template_id: str

    @field_validator("interpreter_type")
    @classmethod
    def check_interpreter_type(cls, interpreter_type, _values) -> InterpreterType:
        if interpreter_type != InterpreterType.CREATE_GENERATOR:
            raise ValueError(
                f"interpreter_type must be {InterpreterType.CREATE_GENERATOR}",
            )
        return interpreter_type


class SwitchToAgentsInterpreterReturnStatus(SwitchInterpreterReturnStatus):
    interpreter_type: InterpreterType = InterpreterType.AGENTS
    agent_id: str

    @field_validator("interpreter_type")
    @classmethod
    def check_interpreter_type(cls, interpreter_type, _values) -> InterpreterType:
        if interpreter_type != InterpreterType.AGENTS:
            raise ValueError(f"interpreter_type must be {InterpreterType.AGENTS}")
        return interpreter_type
