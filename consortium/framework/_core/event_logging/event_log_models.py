from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, JsonValue

from consortium.server.utils import utc_now


class CurrentProgressModel(BaseModel):
    percent_complete: float = Field(ge=0.0, le=100.0, default=0.0)
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=utc_now)


class EventLogEntryType(StrEnum):
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    FAILURE = "FAILURE"
    WARNING = "WARNING"
    ARTIFACT = "ARTIFACT"
    ERROR = "ERROR"


class EventLogEntryModel(BaseModel):
    sequence: int
    event_type: EventLogEntryType
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=utc_now)


class EventLogModel(BaseModel):
    current_progress: CurrentProgressModel | None
    total_count: int
    entries: list[EventLogEntryModel]
