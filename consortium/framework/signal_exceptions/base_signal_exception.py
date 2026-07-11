from pydantic import JsonValue


class BaseSignalException(Exception):
    def __init__(self, message: str, detail: dict[str, JsonValue] | None = None):
        if detail is None:
            detail = {}

        self.message = message
        self.detail = detail

        super().__init__(message)
