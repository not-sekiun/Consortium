from datetime import datetime
from enum import StrEnum

from pydantic import UUID4, BaseModel, JsonValue

from consortium.framework._core.event_logging.event_log_models import EventLogModel
from consortium.server.models.error_models import ErrorModel


class AgentTaskState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ERRORED = "ERRORED"


class AgentTaskStatusModel(BaseModel):
    state: AgentTaskState
    error: ErrorModel | None


class AgentTaskModel(BaseModel):
    task_id: UUID4
    command: str
    arguments: dict[str, JsonValue]
    status: AgentTaskStatusModel
    event_log: EventLogModel
    datetime_created: datetime
    datetime_started: datetime | None = None
    datetime_completed: datetime | None = None
