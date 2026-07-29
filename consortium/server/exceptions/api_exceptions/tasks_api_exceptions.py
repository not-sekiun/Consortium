from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    NotFoundError,
)


class TaskNotFoundError(NotFoundError): ...


class TaskNotQueuedError(ConflictError): ...


class TaskNotTerminalError(ConflictError): ...
