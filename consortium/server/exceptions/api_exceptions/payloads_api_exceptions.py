from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError


class PayloadNotFoundError(NotFoundError):
    code = "PAYLOAD_NOT_FOUND_ERROR"
