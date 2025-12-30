from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.objects.agent_objects import AgentStatus


class ConnectedListenerReferenceModel(BaseModel):
    listener_id: str
    name: str


class AgentModel(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint: str
    agent_type: AgentTypeModel
    user: str | None
    is_admin: bool | None
    os: str | None
    version: str | None
    arch: str | None
    pid: int | None
    locale: str | None
    remote_host_address: str | None
    local_host_address: str | None
    hostname: str | None
    datetime_first_checked_in: str
    datetime_last_checked_in: str
    status: AgentStatus
    connected_listener: ConnectedListenerReferenceModel | None
    agent_data: dict[str, Any] | None
