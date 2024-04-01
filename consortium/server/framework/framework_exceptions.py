from typing import Any

from consortium.server.server_exceptions import ServerException


# Framework exceptions encapsulate the same data as server exceptions, but will not
# automatically run in the server exception handler when raised. Server exceptions
# should only be used when an immediate response is to be expected since raising a
# server exception will also return a response to the client. Framework exceptions are
# raised when the error is not expected to be immediately handled by the server most
# notably during asynchronous runtime.
class FrameworkException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str = "",
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail

        self.status_code = status_code
        self.headers = headers

    def to_json(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "detail": self.detail,
            },
        }


class ListenerStartError(ServerException):
    def __init__(
        self,
        message: str = "The listener could not be started due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_START_ERROR",
            message=message,
            detail=detail,
        )


class ListenerRuntimeError(FrameworkException):
    def __init__(
        self,
        message: str = "The listener encountered a runtime error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_RUNTIME_ERROR",
            message=message,
            detail=detail,
        )


class ListenerStopError(ServerException):
    def __init__(
        self,
        message: str = "The listener could not be stopped due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_STOP_ERROR",
            message=message,
            detail=detail,
        )


class ListenerCancellationError(ServerException):
    def __init__(
        self,
        message: str = "The listener could not be cancelled due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="LISTENER_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorQueueError(ServerException):
    def __init__(
        self,
        message: str = "The agent generator could not be queued due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_QUEUE_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorBuildError(FrameworkException):
    def __init__(self, message: str = "", detail: Any = None):
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_BUILD_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorCompletionError(ServerException):
    def __init__(
        self,
        message: str = "The agent generator could not be completed due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_COMPLETION_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorCancellationError(ServerException):
    def __init__(
        self,
        message: str = "The agent generator could not be cancelled due to an error.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )
