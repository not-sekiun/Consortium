from typing import Any


class BaseFrameworkException(Exception):
    def __init__(
        self,
        code: str,
        message: str = "",
        detail: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


class ListenerStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to start the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="LISTENER_START_ERROR",
            message=message,
            detail=detail,
        )


class ListenerRuntimeError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while the listener was running.",
        detail: Any = None,
    ):
        super().__init__(
            code="LISTENER_RUNTIME_ERROR",
            message=message,
            detail=detail,
        )


class ListenerStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to stop the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="LISTENER_STOP_ERROR",
            message=message,
            detail=detail,
        )


class ListenerCancellationError(BaseFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to cancel the listener.",
        detail: Any = None,
    ):
        super().__init__(
            code="LISTENER_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorStartError(BaseFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to queue the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="AGENT_GENERATOR_QUEUE_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorBuildError(BaseFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while the agent generator was building the agent."
        ),
        detail: Any = None,
    ):
        super().__init__(
            code="AGENT_GENERATOR_BUILD_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorStopError(BaseFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to stop the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="AGENT_GENERATOR_STOP_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorCancellationError(BaseFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to cancel the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            code="AGENT_GENERATOR_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )
