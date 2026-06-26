import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, JsonValue

from consortium.server.models.error_models import ErrorModel


class AgentTaskState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ERRORED = "ERRORED"


class AgentTaskEventType(StrEnum):
    # These task event types are manually emitted by `BaseAgentCapability` authors
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    FAILURE = "FAILURE"
    ARTIFACT = "ARTIFACT"

    # These task event types are automatically emitted by the framework upon
    # unhandled error (`ERROR`) or terminal completion of a task when the method exits
    # (`COMPLETED`)
    ERROR = "ERROR"
    # TODO: Consider remove AgentTaskEventType.COMPLETED it is currently not used and
    #  im not sure if its necessary
    COMPLETED = "COMPLETED"


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


class AgentTaskEventsModel(BaseModel):
    total_count: int
    entries: list[AgentTaskEventModel]


class AgentTaskStatusModel(BaseModel):
    state: AgentTaskState
    error: ErrorModel | None


class AgentTaskModel(BaseModel):
    task_id: uuid.UUID
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatusModel
    current_progress: AgentCurrentProgressModel | None = None
    events: AgentTaskEventsModel
    datetime_created: datetime
    datetime_started: datetime | None = None
    datetime_completed: datetime | None = None


# class AgentCapabilityRuntimeErrorModel(BaseModel):
#     code: str = "AGENT_CAPABILITY_RUNTIME_ERROR"
#     message: str = ""
#     details: dict[str, JsonValue] = {}
