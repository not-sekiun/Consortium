# Errors for the api endpoint /api/listener-templates.
# - HTTPError
#   - NotFoundError
#     - ListenerTemplateNotFoundError
#   - UnprocessableEntityError
#     - ListenerCreationError
#       - InvalidListenerTemplateOptionNameError
#       - InvalidListenerTemplateOptionValueError
from typing import Any

from consortium.server.exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class ListenerTemplateNotFoundError(NotFoundError):
    def __init__(
        self,
        listener_template_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="LISTENER_TEMPLATE_NOT_FOUND_ERROR",
            message=(
                "The requested listener template with the provided listener template "
                f'ID "{listener_template_id}" was not found.'
            ),
            detail={"listener_template_id": listener_template_id},
        )


class ListenerCreationError(UnprocessableEntityError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "LISTENER_CREATION_ERROR",
        message: str = "An error occurred while attempting to create the listener.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class InvalidListenerTemplateOptionNameError(ListenerCreationError):
    def __init__(
        self,
        option_name: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_LISTENER_TEMPLATE_OPTION_NAME_ERROR",
            message=(
                f'The provided listener template option name "{option_name}" is '
                f"invalid"
            ),
            detail={"option_name": option_name},
        )


class InvalidListenerTemplateOptionValueError(ListenerCreationError):
    def __init__(
        self,
        option_name: str,
        option_value: Any,
        exception: Exception,
    ) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_LISTENER_TEMPLATE_OPTION_VALUE_ERROR",
            message=(
                f'The provided listener template option value "{option_value}" for '
                f'option "{option_name}" is invalid'
            ),
            detail={
                "option_name": option_name,
                "option_value": option_value,
                "exception": str(exception),
            },
        )
