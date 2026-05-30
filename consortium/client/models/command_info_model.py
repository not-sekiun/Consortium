from pydantic import BaseModel


class CommandInfo(BaseModel):
    name: str
    description: str
    group: str
    summary: str
