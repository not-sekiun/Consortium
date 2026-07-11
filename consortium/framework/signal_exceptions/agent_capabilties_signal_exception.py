from pydantic import JsonValue

from consortium.framework.signal_exceptions.base_signal_exception import (
    BaseSignalException,
)


class AgentCapabilityLaunchError(BaseSignalException):
    """Raise this exception from `on_launch` to deliberately deny a task from starting
    and report failure to the operator."""

    def __init__(
        self,
        message: str = "An error occurred while launching the agent capability.",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class AgentCapabilityExecutionError(BaseSignalException):
    """Raise this exception from `on_execute` to deliberately stop an executing agent
    capability and report failure to the operator."""

    def __init__(
        self,
        message: str = "An error occurred while executing the agent capability.",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
