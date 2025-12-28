from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    InternalServerError,
    NotFoundError,
    UnprocessableEntityError,
)


class ListenerNotFoundError(NotFoundError): ...


class InvalidListenerParameterNameError(UnprocessableEntityError): ...


class InvalidListenerParameterValueError(UnprocessableEntityError): ...


class ListenerAlreadyRunningError(ConflictError): ...


class ListenerNotRunningError(ConflictError): ...


class ListenerTemplateResolutionError(InternalServerError):
    code = "LISTENER_TEMPLATE_RESOLUTION_ERROR"

    def __init__(
        self,
        listener_type: BaseListenerType,
    ) -> None:
        super().__init__(
            message=(
                "Failed to resolve the listener's listener template for the given "
                f"listener type {listener_type}."
            ),
            detail={"listener_type": listener_type.to_json()},
        )


class ListenerStartError(ConflictError): ...


class ListenerStopError(ConflictError): ...
