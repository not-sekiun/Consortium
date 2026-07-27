from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.listener_and_agent_reference_models import (
    ListenerReferenceModel,
)
from consortium.server.objects.agent_objects import AgentStatus


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
    remote_ip: str | None
    local_ip: str | None
    hostname: str | None
    datetime_first_checked_in: str
    datetime_last_checked_in: str
    status: AgentStatus
    connected_listener: ListenerReferenceModel | None
    agent_data: dict[str, Any] | None
