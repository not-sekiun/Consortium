from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import AgentTypeModel


class AgentTemplateModel(BaseModel):
    name: str
    description: str
    agent_type: AgentTypeModel
    authors: list[str]
    options: dict[str, Any]
    agent_template_id: str
    validating_function: None | str
