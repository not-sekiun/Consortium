from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

SimpleType = str | int | float | bool


class AgentTypeModel(BaseModel):
    name: str
    agent_type_id: str
    # If compatible_listener_type_ids is an empty list it is compatible with no listener
    # types.
    compatible_listener_type_ids: list[str]


class AgentTaskModel(BaseModel):
    command: str = ""
    arguments: list[SimpleType] | dict | None = None
    task_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = datetime.now()


class AgentResultModel(BaseModel):
    task_id: str
    result: SimpleType | dict[str, Any] | list[SimpleType | None] | None = None
    result_id: UUID = Field(default_factory=uuid4)
    finished_at: datetime = datetime.now()
