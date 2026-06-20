import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, JsonValue


class AgentTaskStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"  # TODO: Remove and replace with success failure error

    # TODO: Implement to subsume Result objects
    SUCCEEDED = "SUCCESS"
    FAILED = "FAILURE"
    ERRORED = "ERROR"


# class AgentTaskProgressStatus(StrEnum):
#     SUCCESS = "SUCCESS"
#     FAILURE = "FAILURE"


# class AgentTaskProgressLogEntryModel(BaseModel):
#     # sequence: int  TODO: Remove and just rely on list indices
#     message: str | None = None
#     data: dict[str, JsonValue] = {}
#     status: AgentTaskProgressStatus = AgentTaskProgressStatus.SUCCESS
#     # percent_complete: int | float = Field(ge=0.0, le=100.0) TODO: Remove, percent complete is too domain specific
#     datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskEventType(StrEnum):
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"
    ARTIFACT = "ARTIFACT"


class AgentTaskEventModel(BaseModel):
    sequence: int
    event_type: AgentTaskEventType
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentCurrentProgressModel(BaseModel):
    percent_complete: float = Field(ge=0.0, le=100.0, default=0.0)
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskEventsAPIResponseModel(BaseModel):
    total_count: int
    entries: list[AgentTaskEventModel]


# class AgentTaskCurrentProgressModel(BaseModel):
#     message: str | None = None
#     data: dict[str, JsonValue] = {}
#     status: AgentTaskProgressStatus = AgentTaskProgressStatus.SUCCESS
#     # percent_complete: int | float = Field(ge=0.0, le=100.0, default=0) TODO: Remove, percent complete is too domain specific
#     datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatus = AgentTaskStatus.QUEUED
    current_progress: AgentCurrentProgressModel | None = None
    events: list[AgentTaskEventModel] = []
    datetime_created: datetime = Field(default_factory=datetime.now)
    datetime_started: datetime | None = None


class AgentTaskAPIResponseModel(BaseModel):
    task_id: uuid.UUID
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatus
    current_progress: AgentCurrentProgressModel | None = None
    events: AgentTaskEventsAPIResponseModel
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


# class AgentResultStatus(StrEnum):
#     SUCCESS = "SUCCESS"
#     FAILURE = "FAILURE"
#     ERROR = "ERROR"
#
#
# class AgentResultModel(BaseModel):
#     result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
#     message: str
#     data: dict[str, JsonValue]
#     status: AgentResultStatus
#     datetime_finished: datetime = Field(default_factory=datetime.now)
#
#     # Derived from corresponding `AgentTaskModel`
#     task_id: uuid.UUID
#     command: str
#     arguments: dict[str, JsonValue]
#     datetime_started: datetime
#
#     @computed_field
#     @cached_property
#     def elapsed_seconds(self) -> float:
#         return (self.datetime_finished - self.datetime_started).total_seconds()
