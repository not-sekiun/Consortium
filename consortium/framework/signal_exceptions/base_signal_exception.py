from collections.abc import Sequence
from typing import Self

from pydantic import JsonValue


class BaseSignalException(Exception):
    def __init__(self, message: str, detail: dict[str, JsonValue] | None = None):
        if detail is None:
            detail = {}

        self.message = message
        self.detail = detail

        super().__init__(message)

    @classmethod
    def from_exception(
        cls, exc: Exception, detail: dict[str, JsonValue] | None = None
    ) -> Self:
        return cls(
            message=f"{exc.__class__.__name__}: {exc}",
            detail=detail,
        )

    @classmethod
    def from_exceptions(
        cls, excs: Sequence[Exception], detail: dict[str, JsonValue] | None = None
    ) -> Self:
        if len(excs) == 1:
            return cls.from_exception(excs[0], detail=detail)
        message = "Multiple errors occurred:\n" + "\n".join(
            f"- {type(e).__name__}: {e}" for e in excs
        )
        return cls(message=message, detail=detail)
