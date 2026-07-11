from typing import Any


class BaseFrameworkError(Exception):
    code: str = "BASE_FRAMEWORK_ERROR"

    def __init__(self, message: str = "", detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)
