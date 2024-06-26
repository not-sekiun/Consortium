from typing import Any

from pydantic import BaseModel


class NewAgentGeneratorAttributesRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


class AgentTaskRequestBodyModel(BaseModel):
    command: str
    arguments: dict[str, Any] | list[Any]
