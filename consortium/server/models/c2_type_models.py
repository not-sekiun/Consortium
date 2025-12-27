from pydantic import BaseModel

from consortium.server.models.option_models import OptionModel


class ListenerTypeModel(BaseModel):
    name: str
    registered_compatible_agent_types: list[str]


class AgentCapabilityModel(BaseModel):
    name: str
    description: str
    authors: list[str]
    requires_admin: bool
    is_atomic: bool
    supported_oses: list[str]
    options: dict[str, OptionModel]


class AgentTypeModel(BaseModel):
    name: str
    agent_capabilities: dict[str, AgentCapabilityModel]
