from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import AgentTypeModel


class AgentTemplateModel(BaseModel):
    agent_template_id: str
    label: str
    name: str
    description: str
    version: str
    compatible_framework_version: str
    authors: list[str]
    agent_type: AgentTypeModel
    options: dict[str, Any]
    validating_function: None | str
