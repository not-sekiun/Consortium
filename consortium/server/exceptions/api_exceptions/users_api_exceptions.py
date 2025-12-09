from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class UserNotFoundError(NotFoundError): ...


class EmptyUserDisplayNameError(UnprocessableEntityError): ...
