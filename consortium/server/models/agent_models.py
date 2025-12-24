import uuid
from datetime import datetime
from enum import StrEnum
from functools import cached_property
from typing import Any

from pydantic import BaseModel, Field, computed_field

from consortium.server.models.c2_types_models import AgentTypeModel


class AgentTaskStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    command: str
    arguments: dict[str, Any]
    status: AgentTaskStatus = AgentTaskStatus.QUEUED
    datetime_started: datetime = Field(default_factory=datetime.now)


class AgentResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAIL"
    ERROR = "ERROR"


class AgentResultModel(BaseModel):
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_id: uuid.UUID  # Derived from corresponding `AgentTaskModel`
    command: str  # Derived from corresponding `AgentTaskModel`
    arguments: dict[str, Any]  # Derived from corresponding `AgentTaskModel`
    status: AgentResultStatus
    message: str
    data: dict[str, Any] | list[Any] | None = None
    datetime_started: datetime  # Derived from corresponding `AgentTaskModel`
    datetime_finished: datetime = Field(default_factory=datetime.now)

    @computed_field
    @cached_property
    def elapsed_seconds(self) -> float:
        return (self.datetime_finished - self.datetime_started).total_seconds()


# TODO: Add ability to mark agents as disconnected instead of deregistered. For agents
#  that are just offline
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
    agent_data: dict[str, Any] | None
