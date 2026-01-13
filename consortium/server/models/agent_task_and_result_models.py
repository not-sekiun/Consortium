import uuid
from datetime import datetime
from enum import StrEnum
from functools import cached_property

from pydantic import BaseModel, Field, JsonValue, computed_field


class AgentTaskStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class AgentTaskProgressStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AgentTaskProgressLogModel(BaseModel):
    sequence: int
    message: str | None = None
    data: dict[str, JsonValue] = {}
    status: AgentTaskProgressStatus = AgentTaskProgressStatus.SUCCESS
    percent_complete: int | float = Field(ge=0.0, le=100.0)
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskProgressLogAPIResponseModel(BaseModel):
    total_count: int
    entries: list[AgentTaskProgressLogModel]


class AgentTaskCurrentProgressModel(BaseModel):
    message: str | None = None
    data: dict[str, JsonValue] = {}
    status: AgentTaskProgressStatus = AgentTaskProgressStatus.SUCCESS
    percent_complete: int | float = Field(ge=0.0, le=100.0)
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatus = AgentTaskStatus.QUEUED
    current_progress: AgentTaskCurrentProgressModel | None = None
    progress_log: list[AgentTaskProgressLogModel] = []
    datetime_created: datetime = Field(default_factory=datetime.now)
    datetime_started: datetime | None = None


class AgentTaskAPIResponseModel(BaseModel):
    task_id: uuid.UUID
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatus
    current_progress: AgentTaskCurrentProgressModel | None = None
    progress_log: AgentTaskProgressLogAPIResponseModel
    datetime_created: datetime
    datetime_started: datetime | None = None


# class AgentResultState(StrEnum):
#     SUCCESS = "SUCCESS"
#     FAILURE = "FAILURE"
#     ERROR = "ERROR"
#
#
# class AgentCapabilityRuntimeErrorModel(BaseModel):
#     code: str = "AGENT_CAPABILITY_RUNTIME_ERROR"
#     message: str = ""
#     details: dict[str, JsonValue] = {}
#
#
# class AgentResultStatusModel(BaseModel):
#     state: AgentResultState
#     error: AgentCapabilityRuntimeErrorModel | None = None


class AgentResultStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"


class AgentResultModel(BaseModel):
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    message: str
    data: dict[str, JsonValue]
    status: AgentResultStatus
    datetime_finished: datetime = Field(default_factory=datetime.now)

    # Derived from corresponding `AgentTaskModel`
    task_id: uuid.UUID
    command: str
    arguments: dict[str, JsonValue]
    datetime_started: datetime

    @computed_field
    @cached_property
    def elapsed_seconds(self) -> float:
        return (self.datetime_finished - self.datetime_started).total_seconds()
