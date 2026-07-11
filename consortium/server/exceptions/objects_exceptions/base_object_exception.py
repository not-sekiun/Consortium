from typing import Any


class BaseObjectError(Exception):
    code: str = "BASE_OBJECT_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)
