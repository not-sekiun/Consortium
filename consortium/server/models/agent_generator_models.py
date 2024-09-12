from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import AgentTypeModel
from consortium.server.models.common_models import ErrorModel
from consortium.server.objects.agent_generator_objects import (
    AgentGeneratorBuildStepState,
    AgentGeneratorState,
)


class AgentGeneratorStatusModel(BaseModel):
    state: AgentGeneratorState
    error: ErrorModel | None


class AgentGeneratorBuildStepStatusModel(BaseModel):
    state: AgentGeneratorBuildStepState
    error: ErrorModel | None


class AgentGeneratorBuildStepModel(BaseModel):
    agent_generator_build_step_id: str
    name: str
    description: str
    ignore_failure: bool
    datetime_started: str | None
    datetime_stopped: str | None
    time_elapsed_in_seconds: int | None
    status: AgentGeneratorBuildStepStatusModel


class CreatingAgentTemplateReferenceModel(BaseModel):
    agent_template_id: str
    name: str


class AgentGeneratorModel(BaseModel):
    agent_generator_id: str
    name: str
    description: str
    agent_type: AgentTypeModel
    parameters: dict[str, Any]
    status: AgentGeneratorStatusModel
    datetime_created: str
    agent_generator_build_steps: list[AgentGeneratorBuildStepModel]
    creating_agent_template: CreatingAgentTemplateReferenceModel
