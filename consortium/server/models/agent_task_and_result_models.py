import uuid
from datetime import datetime
from enum import StrEnum
from functools import cached_property
from typing import Any

from pydantic import BaseModel, Field, JsonValue, computed_field


class AgentTaskStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class AgentTaskProgressModel(BaseModel):
    message: str | None = None
    percent_complete: int | float = Field(ge=0.0, le=100.0)
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    command: str
    arguments: dict[str, Any]
    current_progress: AgentTaskProgressModel | None = None
    progress_log: list[AgentTaskProgressModel] = []
    status: AgentTaskStatus = AgentTaskStatus.QUEUED
    datetime_started: datetime = Field(default_factory=datetime.now)


class AgentResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
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
