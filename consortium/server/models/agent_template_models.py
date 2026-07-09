from pydantic import UUID4, BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.option_models import OptionModel


class AgentTemplateModel(BaseModel):
    agent_template_id: UUID4
    label: str
    name: str
    description: str
    version: str
    compatible_framework_version: str
    authors: list[str]
    agent_type: AgentTypeModel
    compatible_listener_types: list[str]
    options: dict[str, OptionModel]
    validating_function: None | str


class LiveAgentTemplateReferenceModel(BaseModel):
    agent_template_id: UUID4
    label: str
    name: str


# Used by payloads to store persistent references on disk to the agent template that
# generated them. Omits `agent_template_id` because that can vary on restart. `label` is
# the persistent identifier for agent templates regardless of their ID
class PersistentAgentTemplateReferenceModel(BaseModel):
    label: str
    name: str
