from typing import Any


class BaseFrameworkException(Exception):
    def __init__(
        self,
        code: str,
        message: str = "",
        detail: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.detail = detail

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }
