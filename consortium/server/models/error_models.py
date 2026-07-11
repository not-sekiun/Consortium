from pydantic import BaseModel, JsonValue


# This model is the generic error model, all responses that need to return some sort of
# error related response should use this model in the form of {"error": ErrorModel}
class ErrorModel(BaseModel):
    code: str
    message: str
    detail: dict[str, JsonValue]
