from typing import Any

from pydantic import BaseModel

from consortium.framework._core.event_logging.event_log_models import EventLogModel
from consortium.server.models.c2_type_models import ListenerTypeModel
from consortium.server.models.component_models import StatusModel
from consortium.server.models.listener_and_agent_reference_models import (
    LiveAgentReferenceModel,
)
from consortium.server.models.listener_template_models import (
    ListenerTemplateReferenceModel,
)


class ListenerModel(BaseModel):
    listener_id: str
    name: str
    description: str
    endpoint: str
    listener_type: ListenerTypeModel
    parameters: dict[str, Any]
    status: StatusModel
    event_log: EventLogModel
    datetime_created: str
    connected_agents: list[LiveAgentReferenceModel]
    creating_listener_template: ListenerTemplateReferenceModel
