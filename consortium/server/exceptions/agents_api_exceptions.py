# Errors for the api endpoint /api/listeners.
# - HTTPError
#   - NotFoundError
#     - AgentNotFoundError
#     - AgentTaskNotFoundError
#     - AgentResultNotFoundError
from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError


class AgentNotFoundError(NotFoundError):
    def __init__(
        self,
        agent_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="AGENT_NOT_FOUND_ERROR",
            message=(
                f'The requested agent with the provided agent ID "{agent_id}" '
                "was not found."
            ),
            detail={"agent_id": agent_id},
        )


class AgentTaskNotFoundError(NotFoundError):
    def __init__(
        self,
        task_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="AGENT_TASK_NOT_FOUND_ERROR",
            message=(
                f'The requested agent task with the provided task ID "{task_id}" was '
                f"not found."
            ),
            detail={"task_id": task_id},
        )


class AgentResultNotFoundError(NotFoundError):
    def __init__(
        self,
        task_id_or_result_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="AGENT_RESULT_NOT_FOUND_ERROR",
            message=(
                f"The requested agent result with the provided task ID or result ID "
                f'"{task_id_or_result_id}" was not found.'
            ),
            detail={"task_id_or_result_id": task_id_or_result_id},
        )
