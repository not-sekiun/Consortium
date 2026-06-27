from datetime import datetime

from pydantic import UUID4, BaseModel, JsonValue

from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.models.c2_type_models import AgentTypeModel


class PayloadModel(BaseModel):
    payload_id: UUID4
    name: str | None
    description: str
    size: int | None
    exists_on_disk: bool
    datetime_created: datetime
    datetime_modified: datetime
    md5_checksum: str | None
    is_directory: bool
    agent_type: AgentTypeModel
    agent_template: AgentTemplateModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]
