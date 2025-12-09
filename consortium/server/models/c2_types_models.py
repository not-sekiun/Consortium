from typing import Any

from pydantic import BaseModel


class CompatibleAgentTypeModel(BaseModel):
    agent_type_id: str
    name: str


class ListenerTypeModel(BaseModel):
    listener_type_id: str
    name: str
    # If `compatible_agent_types` is an empty list it is compatible with no agent
    # types.
    compatible_agent_types: list[CompatibleAgentTypeModel]


class CompatibleListenerTypeModel(BaseModel):
    listener_type_id: str
    name: str


class AgentCapabilityModel(BaseModel):
    name: str
    description: str
    options: dict[str, Any]
    authors: list[str]
    requires_admin: bool
    supported_oses: list[str]


class AgentTypeModel(BaseModel):
    agent_type_id: str
    name: str
    # If `compatible_listener_types` is an empty list it is compatible with no listener
    # types.
    compatible_listener_types: list[CompatibleListenerTypeModel]
    agent_capabilities: dict[str, AgentCapabilityModel]
