from typing import Any

from pydantic import BaseModel


# This model is the generic error model, all responses that need to return some sort of
# error related response should use this model in the form of {"error": ErrorModel}
class ErrorModel(BaseModel):
    code: str
    message: str
    detail: Any
