from typing import Any

from pydantic import BaseModel


class AgentTaskRequestBodyModel(BaseModel):
    command: str
    arguments: dict[str, Any] | list[Any]
