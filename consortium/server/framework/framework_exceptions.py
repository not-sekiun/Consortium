from typing import Any

from consortium.server.server_exceptions import ServerException

# class _DetailedException(Exception):
#     def __init__(
#         self, message: str = "", detail: Any | None = None, *args: list[Any]
#     ) -> None:
#         super().__init__(*args)
#         error_name = type(self).__name__
#         # it is conventional to use SCREAMING_SNAKE_CASE for error names in REST APIs
#         # over python's convention of using PascalCase for class names, so we do the
#         # conversion here once in the __init__ method. Name shadowing of type() will not
#         # occur here
#         self.type = ""
#         for char_index, char_value in enumerate(error_name):
#             if char_value.isupper() and char_index not in (0, len(error_name) - 1):
#                 self.type += "_" + char_value
#             else:
#                 self.type += char_value.upper()
#         self.message = message
#         self.detail = detail
#
#     def to_json(self) -> dict[str, Any]:
#         return {
#             "type": self.type,
#             "message": self.message,
#             "detail": self.detail,
#         }


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


class ListenerRuntimeError(ServerException):
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


class AgentGeneratorBuildError(ServerException):
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
