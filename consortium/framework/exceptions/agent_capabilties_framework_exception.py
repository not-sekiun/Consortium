from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class AgentCapabilityTaskingError(BaseRaiseOnlyFrameworkException):
    code = "AGENT_CAPABILITY_TASKING_ERROR"

    def __init__(
        self,
        message: str = "An error occurred while attempting to task the agent.",
        detail: str = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
