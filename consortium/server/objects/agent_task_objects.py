import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, JsonValue

from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    AgentCapabilityRuntimeError,
)

# from consortium.server.models.agent_task_models import (
#     AgentTaskProgressLogEntryModel,
#     AgentTaskProgressStatus,
# )


class AgentTaskState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ERRORED = "ERRORED"


class AgentTaskStatus:
    _VALID_STATE_TRANSITIONS = {
        AgentTaskState.QUEUED: {AgentTaskState.RUNNING},
        AgentTaskState.RUNNING: {
            AgentTaskState.SUCCEEDED,
            AgentTaskState.FAILED,
            AgentTaskState.ERRORED,
        },
        AgentTaskState.SUCCEEDED: {},
        AgentTaskState.FAILED: {},
        AgentTaskState.ERRORED: {},
    }

    def __init__(self):
        self.state = AgentTaskState.QUEUED
        self.error = None

    def to_json(self):
        return {
            "state": str(self.state),
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "detail": self.error.detail,
            }
            if isinstance(self.error, AgentCapabilityRuntimeError)  # TODO: Add error
            else None,
        }

    def _transition_to_state(
        self,
        new_state: AgentTaskState,
        error: AgentCapabilityRuntimeError | None = None,
    ):
        if new_state not in self._VALID_STATE_TRANSITIONS[self.state]:
            raise AssertionError(
                f"Invalid status transition from current status '{self.state}' to new "
                f"status '{new_state}'.",
            )
        if (
            new_state in (AgentTaskState.FAILED, AgentTaskState.ERRORED)
            and error is None
        ):
            raise AssertionError(
                f"When transitioning to the '{new_state}' status, an error must be "
                f"provided.",
            )
        if (
            new_state not in (AgentTaskState.FAILED, AgentTaskState.ERRORED)
            and error is not None
        ):
            raise AssertionError(
                f"When transitioning to the '{new_state}' status, no error should be "
                f"provided.",
            )
        self.state = new_state
        self.error = error

    def _transition_to_queued(self) -> None:
        self._transition_to_state(new_state=AgentTaskState.QUEUED)

    def _transition_to_running(self) -> None:
        self._transition_to_state(new_state=AgentTaskState.RUNNING)

    def _transition_to_succeeded(self) -> None:
        self._transition_to_state(new_state=AgentTaskState.SUCCEEDED)

    def _transition_to_failed(self, error: AgentCapabilityRuntimeError) -> None:
        self._transition_to_state(new_state=AgentTaskState.FAILED, error=error)

    def _transition_to_errored(self, error: AgentCapabilityRuntimeError) -> None:
        self._transition_to_state(new_state=AgentTaskState.ERRORED, error=error)


class AgentTaskEventType(StrEnum):
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"
    ARTIFACT = "ARTIFACT"


class AgentTaskEvent(BaseModel):
    event_type: AgentTaskEventType
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentProgressUpdate(BaseModel):
    percent_complete: float = Field(ge=0.0, le=100.0, default=0.0)
    message: str | None = None
    data: dict[str, JsonValue] = {}
    datetime_reported: datetime = Field(default_factory=datetime.now)


class AgentTask:
    def __init__(
        self,
        command: str,
        arguments: dict[str, Any],
    ):
        self.task_id = uuid.uuid4()
        self.command = command
        self.arguments = arguments
        self.status = AgentTaskStatus()
        self.current_progress = None
        self.events = []
        self.datetime_created = datetime.now()
        self.datetime_started = None

    def append_event(
        self,
        event_type: AgentTaskEventType,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            AgentTaskEvent(
                event_type=event_type,
                message=message,
                data=data or {},
            )
        )

    def update_progress(
        self,
        percent_complete: float = 0,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.current_progress = AgentProgressUpdate(
            percent_complete=percent_complete,
            message=message,
            data=data or {},
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "status": self.status.to_json(),
            "current_progress": self.current_progress.model_dump()
            if self.current_progress is not None
            else None,
            "events": [event.model_dump() for event in self.events],
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_started": self.datetime_started.isoformat()
            if self.datetime_started is not None
            else None,
        }
