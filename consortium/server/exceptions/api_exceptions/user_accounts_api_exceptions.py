from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)


class UserAccountNotFoundError(NotFoundError): ...


class IdenticalUserAccountUsernameError(UnprocessableEntityError): ...


class IdenticalUserAccountPasswordError(UnprocessableEntityError): ...


class IdenticalUserAccountRoleError(UnprocessableEntityError): ...


class EmptyUserAccountUsernameError(UnprocessableEntityError): ...


class EmptyUserAccountPasswordError(UnprocessableEntityError): ...


class InvalidUserAccountRoleError(UnprocessableEntityError): ...


class UserAccountUsernameAlreadyExistsError(UnprocessableEntityError): ...


class UserAccountAuthenticationError(ForbiddenError): ...
