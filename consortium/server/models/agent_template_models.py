from pydantic import BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.option_models import OptionModel


class AgentTemplateModel(BaseModel):
    agent_template_id: str
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
