from typing import Any

from pydantic import BaseModel

from consortium.framework._components._status import State


class ErrorModel(BaseModel):
    message: str
    detail: Any


class StatusModel(BaseModel):
    state: State
    error: ErrorModel | None
