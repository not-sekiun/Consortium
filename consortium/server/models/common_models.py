from typing import Any

from pydantic import BaseModel


# This model is the generic error model, all responses that need to return some sort of
# error related response should use this model in the form of {"error": ErrorModel}
class ErrorModel(BaseModel):
    code: str
    message: str
    detail: Any


# TODO: Remove in favor of just response endpoints
# These models are defined for api endpoints that do not respond with any data for an
# operation. For example, sending a DELETE or PUT to /api/listeners/{listener_id}. Here
# the response is binary, either the operation succeeded or it failed
class SuccessResponseModel(BaseModel):
    success: bool = True
