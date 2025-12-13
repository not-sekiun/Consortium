import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from consortium.server.models.c2_types_models import AgentTypeModel


class AgentTaskState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    command: str
    arguments: dict[str, Any]
    state: AgentTaskState = AgentTaskState.QUEUED
    datetime_started: datetime = Field(default_factory=datetime.now)


class AgentResultModel(BaseModel):
    result_id: uuid.UUID
    success: bool
    message: str
    data: dict[str, Any] | list[Any] | None = None
    task_id: uuid.UUID
    datetime_finished: datetime = Field(default_factory=datetime.now)


# TODO: Add ability to mark agents as disconnected instead of deregistered. For agents
#  that are just offline
class AgentModel(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint: str
    agent_type: AgentTypeModel
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
    agent_data: dict[str, Any] | None
