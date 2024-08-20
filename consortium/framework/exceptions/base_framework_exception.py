from typing import Any


class BaseFrameworkException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BaseRaiseOnlyFrameworkException(BaseFrameworkException):
    code: str

    def __init__(self, message: str, detail: Any = None):
        self.message = message
        self.detail = detail
        super().__init__(message)

    def to_json(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "detail": self.detail,
        }


class BaseCatchOnlyFrameworkException(BaseFrameworkException): ...
