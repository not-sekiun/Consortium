from pydantic import BaseModel

from consortium.server.models.option_models import OptionModel
from consortium.server.objects.mitre_attack_objects import MitreAttackTechnique


class ListenerTypeModel(BaseModel):
    name: str
    registered_compatible_agent_types: list[str]


class AgentCapabilityModel(BaseModel):
    name: str
    description: str
    authors: list[str]
    requires_admin: bool
    supported_oses: list[str]
    mitre_attack_techniques: list[MitreAttackTechnique]
    options: dict[str, OptionModel]
    validating_function: str | None


class AgentTypeModel(BaseModel):
    name: str
    agent_capabilities: dict[str, AgentCapabilityModel]
