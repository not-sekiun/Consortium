# Errors for the endpoint /api/agent-templates.
# - HTTPError
#   - NotFoundError
#     - AgentTemplateNotFoundError
#   - UnprocessableEntityError
#     - AgentGeneratorCreationError
#       - InvalidAgentTemplateOptionNameError
#       - InvalidAgentTemplateOptionValueError
from typing import Any

from consortium.server.exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class AgentTemplateNotFoundError(NotFoundError):
    def __init__(
        self,
        agent_template_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="AGENT_TEMPLATE_NOT_FOUND_ERROR",
            message=(
                "The requested agent template with the provided agent template ID "
                f'"{agent_template_id}" was not found.'
            ),
            detail={"agent_template_id": agent_template_id},
        )


class AgentGeneratorCreationError(UnprocessableEntityError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "AGENT_GENERATOR_CREATION_ERROR",
        message: str = (
            "An error occurred while attempting to create the agent generator."
        ),
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class InvalidAgentTemplateOptionNameError(AgentGeneratorCreationError):
    def __init__(
        self,
        option_name: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_AGENT_TEMPLATE_OPTION_NAME_ERROR",
            message=(
                f'The provided agent template option name "{option_name}" is '
                f"invalid"
            ),
            detail={"option_name": option_name},
        )


class InvalidAgentTemplateOptionValueError(AgentGeneratorCreationError):
    def __init__(
        self,
        option_name: str,
        option_value: Any,
        exception: Exception,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_AGENT_TEMPLATE_OPTION_VALUE_ERROR",
            message=(
                f'The provided agent template option value "{option_value}" for '
                f'option "{option_name}" is invalid'
            ),
            detail={
                "option_name": option_name,
                "option_value": option_value,
                "exception": str(exception),
            },
        )
