import uuid
from typing import Any

from pydantic import BaseModel, Field

from consortium.server.models.common_models import ErrorModel
from consortium.server.objects.listener_objects import ListenerState


class ListenerTypeModel(BaseModel):
    name: str
    description: str
    listener_type_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class _ListenerStatusModel(BaseModel):
    state: ListenerState
    error: ErrorModel | None


class ListenerModel(BaseModel):
    name: str
    endpoint: str
    listener_type: ListenerTypeModel
    options: dict[str, Any]
    listener_id: str
    status: _ListenerStatusModel
