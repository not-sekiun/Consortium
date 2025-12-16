from typing import Any

from pydantic import BaseModel


class ListenerTypeModel(BaseModel):
    name: str


class AgentCapabilityModel(BaseModel):
    name: str
    description: str
    authors: list[str]
    requires_admin: bool
    is_atomic: bool
    supported_oses: list[str]
    options: dict[str, Any]


class AgentTypeModel(BaseModel):
    name: str
    agent_capabilities: dict[str, AgentCapabilityModel]
