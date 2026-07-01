import uuid
from datetime import datetime
from typing import Any

from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    AgentCapabilityExecutionError,
)
from consortium.server.models.agent_task_models import (
    AgentCurrentProgressModel,
    AgentTaskEventModel,
    AgentTaskEventType,
    AgentTaskState,
)


# TODO: Find some way to subsume into Component Status, Component Status should be made
#  more reusable across different objects this is some dogshit code
class AgentTaskStatus:
    _VALID_STATE_TRANSITIONS = {
        # A task can reach a terminal state directly from QUEUED when it never gets
        # acknowledged by the agent (denied at launch, timed out before pickup, dropped
        # or completed server side). RUNNING remains a distinct milestone meaning the
        # agent popped the launch message, `datetime_started` being None discriminates a
        # task that never ran from one that ran and finished.
        AgentTaskState.QUEUED: {
            AgentTaskState.RUNNING,
            AgentTaskState.SUCCEEDED,
            AgentTaskState.FAILED,
            AgentTaskState.ERRORED,
        },
        AgentTaskState.RUNNING: {
            AgentTaskState.SUCCEEDED,
            AgentTaskState.FAILED,
            AgentTaskState.ERRORED,
        },
        AgentTaskState.SUCCEEDED: set(),
        AgentTaskState.FAILED: set(),
        AgentTaskState.ERRORED: set(),
    }

    def __init__(self):
        self.state = AgentTaskState.QUEUED
        self.error = None

    def __str__(self) -> str:
        return f"{self.state}: {self.error}" if self.error is not None else self.state

    def __repr__(self) -> str:
        return f"Status(state={self.state!r}, error={self.error!r})"

    def to_json(self):
        return {
            "state": str(self.state),
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "detail": self.error.detail,
            }
            if isinstance(self.error, AgentCapabilityExecutionError)  # TODO: Add error
            else None,
        }

    def _transition_to_state(
        self,
        new_state: AgentTaskState,
        error: AgentCapabilityExecutionError | None = None,
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

    def _transition_to_failed(self, error: AgentCapabilityExecutionError) -> None:
        self._transition_to_state(new_state=AgentTaskState.FAILED, error=error)

    def _transition_to_errored(self, error: AgentCapabilityExecutionError) -> None:
        self._transition_to_state(new_state=AgentTaskState.ERRORED, error=error)


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
        self.datetime_created = datetime.now()
        self.datetime_started = None
        self.datetime_completed = None

        self._sequence: int = 0
        self._events: list[AgentTaskEventModel] = []  # TODO: Move to db when possible

    def __str__(self) -> str:
        return f"'{self.command}' ({self.task_id})"

    def __repr__(self) -> str:
        return (
            f"AgentTask("
            f"task_id={self.task_id!r}, "
            f"command={self.command!r}, "
            f"arguments={self.arguments!r}, "
            f"status={self.status!r},"
            f")"
        )

    @property
    def events_total_count(self) -> int:
        return len(self._events)

    def get_events(
        self, limit: int = 10, offset: int | None = None
    ) -> list[AgentTaskEventModel]:
        total_count = len(self._events)

        if total_count == 0:
            filtered_events = []
        else:
            # Get min and max sequence numbers
            sequences = [event.sequence for event in self._events]
            min_seq = min(sequences)
            max_seq = max(sequences)

            # If offset is None, return the tail (entries with highest sequence numbers)
            if offset is None:
                # Get entries with the highest sequence numbers, up to limit
                start_seq = max(min_seq, max_seq - limit + 1)
                filtered_events = [
                    event for event in self._events if event.sequence >= start_seq
                ]
                # Sort by sequence and take the last limit entries
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)[
                    -limit:
                ]
            # Handle negative offset (from max sequence)
            elif offset < 0:
                start_seq = max(min_seq, max_seq + offset + 1)
                end_seq = start_seq + limit - 1
                filtered_events = [
                    event
                    for event in self._events
                    if start_seq <= event.sequence <= end_seq
                ]
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)
            else:
                # Filter entries where sequence >= offset
                start_seq = offset
                end_seq = offset + limit - 1
                filtered_events = [
                    event
                    for event in self._events
                    if start_seq <= event.sequence <= end_seq
                ]
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)

        return filtered_events

    def append_event(
        self,
        event_type: AgentTaskEventType,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self._events.append(
            AgentTaskEventModel(
                sequence=self._sequence,
                event_type=event_type,
                message=message,
                data=data or {},
            )
        )
        self._sequence += 1

    def update_progress(
        self,
        percent_complete: float = 0,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.current_progress = AgentCurrentProgressModel(
            percent_complete=percent_complete,
            message=message,
            data=data or {},
        )

    def to_json(self, limit: int = 10, offset: int | None = None) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "status": self.status.to_json(),
            "current_progress": self.current_progress.model_dump(mode="json")
            if self.current_progress is not None
            else None,
            "events": {
                "total_count": self.events_total_count,
                "entries": [
                    event.model_dump(mode="json")
                    for event in self.get_events(limit=limit, offset=offset)
                ],
            },
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_started": self.datetime_started.isoformat()
            if self.datetime_started is not None
            else None,
            "datetime_completed": self.datetime_completed.isoformat()
            if self.datetime_completed is not None
            else None,
        }
