from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)


class ListenerNotFoundError(NotFoundError): ...


class InvalidListenerParameterNameError(UnprocessableEntityError): ...


class InvalidListenerParameterValueError(UnprocessableEntityError): ...


class ListenerAlreadyRunningError(ConflictError): ...


class ListenerNotRunningError(ConflictError): ...


class ListenerStartError(ConflictError): ...


class ListenerStopError(ConflictError): ...
