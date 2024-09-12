from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import AgentTypeModel


class AgentTemplateModel(BaseModel):
    agent_template_id: str
    name: str
    description: str
    agent_type: AgentTypeModel
    authors: list[str]
    options: dict[str, Any]
    validating_function: None | str
