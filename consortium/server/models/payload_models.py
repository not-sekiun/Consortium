from pydantic import JsonValue

from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.repository_models import RepositoryResourceModel


class PayloadModel(RepositoryResourceModel):
    agent_type: AgentTypeModel
    agent_template: AgentTemplateModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]
