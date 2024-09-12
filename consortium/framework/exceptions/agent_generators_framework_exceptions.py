from typing import Any

from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class AgentGeneratorStartError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to queue the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )


class AgentGeneratorBuildError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while the agent generator was building the agent."
        ),
        detail: Any = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
        )


class AgentGeneratorStopError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to stop the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
