from typing import Any

from pydantic import BaseModel

from consortium.server.models.common_models import ErrorModel
from consortium.server.objects.listener_objects import ListenerState


class ListenerTypeModel(BaseModel):
    name: str
    listener_type_id: str
    # If compatible_agent_type_ids is an empty list it is compatible with no agent
    # types.
    compatible_agent_type_ids: list[str]


class _ListenerStatusModel(BaseModel):
    state: ListenerState
    error: ErrorModel | None


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
