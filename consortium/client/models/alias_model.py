from pydantic import BaseModel


class Alias(BaseModel):
    command: str
    is_global: bool
