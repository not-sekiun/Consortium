import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_logger import EventLogger
from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilitiesFrameworkError,
)
from consortium.server.models.agent_task_models import (
    AgentTaskState,
)
from consortium.server.models.logging_models import LoggerType


# TODO: Find some way to subsume into Component Status, Component Status should be made
#  more reusable across different objects this is some dogshit code
class AgentTaskStatus:
    _valid_state_transitions = {
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
            if isinstance(self.error, AgentCapabilitiesFrameworkError)
            else None,
        }

    def _transition_to_state(
        self,
        new_state: AgentTaskState,
        error: AgentCapabilitiesFrameworkError | None = None,
    ):
        if new_state not in self._valid_state_transitions[self.state]:
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

    def _transition_to_failed(self, error: AgentCapabilitiesFrameworkError) -> None:
        self._transition_to_state(new_state=AgentTaskState.FAILED, error=error)

    def _transition_to_errored(self, error: AgentCapabilitiesFrameworkError) -> None:
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
        self.datetime_created = datetime.now()
        self.datetime_started = None
        self.datetime_completed = None
        self._logger = logger.bind(
            logger_name=f"Agent Task - {self}",
            logger_type=LoggerType.AGENT_TASK_LOGGER,
        )
        self.event_logger = EventLogger(
            event_log=EventLog(subject_id=self.task_id), logger=self._logger
        )

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

    def to_json(self, limit: int = 10, offset: int | None = None) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "status": self.status.to_json(),
            "event_log": self.event_logger.to_json(limit=limit, offset=offset),
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_started": self.datetime_started.isoformat()
            if self.datetime_started is not None
            else None,
            "datetime_completed": self.datetime_completed.isoformat()
            if self.datetime_completed is not None
            else None,
        }
