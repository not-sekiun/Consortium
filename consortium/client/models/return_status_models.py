# from enum import StrEnum
# from typing import Any
#
# from pydantic import BaseModel
#
#
# class InterpreterType(StrEnum):
#     HOME_INTERPRETER = "HOME_INTERPRETER"
#     LISTENERS_INTERPRETER = "LISTENERS_INTERPRETER"
#     AGENTS_INTERPRETER = "AGENTS_INTERPRETER"
#     GENERATORS_INTERPRETER = "GENERATORS_INTERPRETER"
#     USE_LISTENER_TEMPLATE_INTERPRETER = "USE_LISTENER_TEMPLATE_INTERPRETER"
#     USE_AGENT_TEMPLATE_INTERPRETER = "USE_AGENT_TEMPLATE_INTERPRETER"
#     INTERACT_AGENT_INTERPRETER = "INTERACT_AGENT_INTERPRETER"
#
#
# class ReturnStatusType(StrEnum):
#     CONTINUE = "CONTINUE"
#     EXIT_CLIENT = "EXIT_CLIENT"
#     SWITCH_INTERPRETER = "SWITCH_INTERPRETER"
#     # Exit without switching client sessions, returns back to the disconnected
#     # interpreter
#     EXIT_CLIENT_SESSION = "EXIT_CLIENT_SESSION"
#     # Exit the current client session and explicitly switch to another client session
#     SWITCH_CLIENT_SESSION = "SWITCH_CLIENT_SESSION"
#
#
# class ReturnStatus(BaseModel):
#     type: ReturnStatusType
#     data: Any | None = None
