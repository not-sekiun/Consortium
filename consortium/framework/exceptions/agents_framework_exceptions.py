from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
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
        self.code = "AGENT_GENERATOR_QUEUE_ERROR"
        super().__init__(
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
        self.code = "AGENT_GENERATOR_BUILD_ERROR"
        super().__init__(
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
        self.code = "AGENT_GENERATOR_STOP_ERROR"
        super().__init__(
            message=message,
            detail=detail,
        )
