from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import ListenerTypeModel
from consortium.server.objects.listener_objects import ListenerState


class _ListenerErrorModel(BaseModel):
    message: str
    detail: Any


class _ListenerStatusModel(BaseModel):
    state: ListenerState
    error: _ListenerErrorModel | None


class ListenerModel(BaseModel):
    name: str
    description: str
    endpoint: str
    listener_type: ListenerTypeModel
    parameters: dict[str, Any]
    listener_id: str
    status: _ListenerStatusModel
    agent_ids: list[str]
    datetime_created: str
