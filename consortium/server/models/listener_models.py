from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_type_models import ListenerTypeModel
from consortium.server.models.component_models import StatusModel


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
    status: StatusModel
    datetime_created: str
    connected_agents: list[ConnectedAgentReferenceModel]
    creating_listener_template: CreatingListenerTemplateReferenceModel
