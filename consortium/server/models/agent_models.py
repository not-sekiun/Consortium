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
    arguments: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    state: AgentTaskState = AgentTaskState.QUEUED


class AgentResultModel(BaseModel):
    result_id: UUID = Field(default_factory=uuid4)
    result: dict[str, Any] = Field(default_factory=dict)
    finished_at: datetime = Field(default_factory=datetime.now)
    task_id: str


class AgentModel(BaseModel):
    agent_id: str
    name: str
    description: str
