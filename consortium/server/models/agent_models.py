import uuid
from copy import deepcopy
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
    started_at: datetime = Field(default_factory=datetime.now)


class AgentResultModel(BaseModel):
    result_id: uuid.UUID
    success: bool
    message: str
    data: dict[str, Any] | list[Any] | None = None
    task_id: uuid.UUID
    finished_at: datetime = Field(default_factory=datetime.now)


class AgentTaskMessageModel(BaseModel):
    task_id: uuid.UUID
    command: str
    arguments: dict[str, Any]
    data: dict[str, Any] = Field(default_factory=dict)

    def create_new_related_task_message(self):
        new_task_message_model = deepcopy(self)
        new_task_message_model.data = {}
        return new_task_message_model


class AgentResultMessageModel(BaseModel):
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_id: uuid.UUID
    success: bool
    message: str
    data: dict[str, Any]

    def create_new_related_result_message(self):
        new_result_message_model = deepcopy(self)
        new_result_message_model.data = {}
        return new_result_message_model


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
    datetime_first_checked_in: str
    datetime_last_checked_in: str
    agent_data: dict[str, Any] | None
