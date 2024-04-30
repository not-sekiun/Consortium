# Errors for the endpoint /api/agent-generators.
# - HTTPError
#   - NotFoundError
#     - AgentGeneratorNotFoundError
# - AgentGeneratorError
#  - AgentGeneratorStateError
#    - AgentGeneratorAlreadyRunningError
#    - AgentGeneratorNotRunningError
#  - AgentGeneratorOperationError
#    - AgentGeneratorStartError
#    - AgentGeneratorBuildError
#    - AgentGeneratorStopError
#    - AgentGeneratorCancellationError
from typing import Any

from consortium.server.exceptions.base_server_exception import BaseServerException
from consortium.server.exceptions.http_exceptions import (
    InternalServerError,
    NotFoundError,
)


class AgentGeneratorNotFoundError(NotFoundError):
    def __init__(
        self,
        agent_generator_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="AGENT_GENERATOR_NOT_FOUND_ERROR",
            message=(
                "The requested agent generator with the provided agent generator ID "
                f'"{agent_generator_id}" was not found.'
            ),
            detail={"agent_generator_id": agent_generator_id},
        )


class AgentGeneratorError(BaseServerException):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "AGENT_GENERATOR_ERROR",
        message: str = "An agent generator error occurred.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class AgentGeneratorStateError(AgentGeneratorError):
    def __init__(
        self,
        status_code: int = 409,
        code: str = "AGENT_GENERATOR_STATE_ERROR",
        message: str = (
            "An agent generator error occurred due to a conflict in the agent "
            "generator's state."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class AgentGeneratorAlreadyRunningError(AgentGeneratorStateError):
    def __init__(
        self,
        message: str = (
            "The agent generator is already running. Stop or wait for it to "
            "complete before performing this operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="AGENT_GENERATOR_ALREADY_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorNotRunningError(AgentGeneratorStateError):
    def __init__(
        self,
        message: str = (
            "The agent generator is not running. Start it before performing this "
            "operation."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="AGENT_GENERATOR_NOT_RUNNING_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorOperationError(AgentGeneratorError):
    def __init__(
        self,
        status_code: int = 400,
        code: str = "AGENT_GENERATOR_OPERATION_ERROR",
        message: str = "An agent generator error occurred while it was in operation.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class AgentGeneratorStartError(AgentGeneratorOperationError):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to queue the agent generator."
        ),
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_QUEUE_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorBuildError(AgentGeneratorOperationError):
    def __init__(
        self,
        message: str = (
            "An error occurred while the agent generator was building the agent."
        ),
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_BUILD_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorStopError(AgentGeneratorOperationError):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to stop the agent generator."
        ),
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_STOP_ERROR",
            message=message,
            detail=detail,
        )


class AgentGeneratorCancellationError(AgentGeneratorOperationError):
    def __init__(
        self,
        message: str = (
            "An error occurred while attempting to cancel the agent generator."
        ),
        detail: Any = None,
    ):
        super().__init__(
            status_code=400,
            code="AGENT_GENERATOR_CANCELLATION_ERROR",
            message=message,
            detail=detail,
        )
