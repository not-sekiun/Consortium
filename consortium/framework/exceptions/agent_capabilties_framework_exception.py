from consortium.framework.exceptions.base_framework_exception import (
    BaseRaiseOnlyFrameworkException,
)


class AgentCapabilityTaskingError(BaseRaiseOnlyFrameworkException):
    def __init__(
        self,
        message: str = "An error occurred while attempting to task the agent.",
        detail: str = None,
    ) -> None:
        super().__init__(
            message=message,
            detail=detail,
        )
