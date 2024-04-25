from typing import Any

from pydantic import BaseModel

from consortium.server.models.agent_models import AgentTypeModel
from consortium.server.models.common_models import ErrorModel
from consortium.server.objects.agent_generator_objects import AgentGeneratorState


class _AgentGeneratorStatusModel(BaseModel):
    state: AgentGeneratorState
    error: ErrorModel | None


class AgentGeneratorModel(BaseModel):
    agent_generator_id: str
    name: str
    description: str
    status: _AgentGeneratorStatusModel
    agent_type: AgentTypeModel
    parameters: dict[str, Any]
