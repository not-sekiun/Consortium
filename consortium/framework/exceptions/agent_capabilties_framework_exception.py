from pydantic import JsonValue

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class AgentCapabilityLaunchError(BaseRaiseOnlyFrameworkException):
    """Raise this exception from `on_launch` to deliberately deny a task from starting
    and report failure to the operator."""

    def __init__(
        self,
        message: str = "An error occurred while launching the agent capability.",
        detail: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class AgentCapabilityExecutionError(BaseRaiseOnlyFrameworkException):
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
