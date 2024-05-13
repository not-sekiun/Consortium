from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentTaskState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class AgentTaskModel(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    command: str
    arguments: dict[str, Any] | list[Any]
    started_at: datetime = Field(default_factory=datetime.now)
    state: AgentTaskState = AgentTaskState.QUEUED


class AgentResultState(StrEnum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class AgentResultModel(BaseModel):
    result_id: UUID = Field(default_factory=uuid4)
    state: AgentResultState
    result: dict[str, Any] | list[Any]
    task_id: str
    finished_at: datetime = Field(default_factory=datetime.now)


class AgentModel(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint: str
    agent_data: dict[str, Any]
    datetime_first_checked_in: str
    datetime_last_checked_in: str
