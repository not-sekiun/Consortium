from typing import Any

from pydantic import BaseModel

# from consortium.framework.agents.agent_generator_objects import (
#     AgentGeneratorBuildStepState,
# )
from consortium.framework._components._component_status import State
from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.common_models import ErrorModel
from consortium.server.models.component_models import StatusModel


class AgentGeneratorBuildStepStatusModel(BaseModel):
    state: State
    error: ErrorModel | None


class AgentGeneratorBuildStepModel(BaseModel):
    agent_generator_build_step_id: str
    name: str
    description: str
    datetime_started: str | None
    datetime_stopped: str | None
    time_elapsed_in_seconds: float | None
    status: AgentGeneratorBuildStepStatusModel


class CreatingAgentTemplateReferenceModel(BaseModel):
    agent_template_id: str
    label: str
    name: str


class AgentGeneratorModel(BaseModel):
    agent_generator_id: str
    name: str
    description: str
    agent_type: AgentTypeModel
    compatible_listener_types: list[str]
    parameters: dict[str, Any]
    status: StatusModel
    datetime_created: str
    agent_generator_build_steps: list[AgentGeneratorBuildStepModel]
    creating_agent_template: CreatingAgentTemplateReferenceModel
