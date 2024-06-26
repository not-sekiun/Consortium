from typing import Any

from consortium.server.framework._exceptions.base_framework_exception import (
    BaseFrameworkException,
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
