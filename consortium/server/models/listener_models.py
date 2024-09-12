from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import ListenerTypeModel
from consortium.server.objects.listener_objects import ListenerState


class ListenerErrorModel(BaseModel):
    message: str
    detail: Any


class ListenerStatusModel(BaseModel):
    state: ListenerState
    error: ListenerErrorModel | None


class ConnectedAgentReferenceModel(BaseModel):
    agent_id: str
    name: str


class CreatingListenerTemplateReferenceModel(BaseModel):
    listener_template_id: str
    name: str


class ListenerModel(BaseModel):
    listener_id: str
    name: str
    description: str
    endpoint: str
    listener_type: ListenerTypeModel
    parameters: dict[str, Any]
    status: ListenerStatusModel
    datetime_created: str
    connected_agents: list[ConnectedAgentReferenceModel]
    creating_listener_template: CreatingListenerTemplateReferenceModel
