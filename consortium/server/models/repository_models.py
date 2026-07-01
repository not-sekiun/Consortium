from datetime import datetime

from pydantic import UUID4, BaseModel, Field, JsonValue

from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.models.c2_type_models import AgentTypeModel


class _ResourceModel(BaseModel):
    name: str | None
    description: str
    size: int | None
    exists_on_disk: bool
    datetime_created: datetime
    datetime_modified: datetime
    md5_checksum: str | None
    is_directory: bool


class RepositoryResourceModel(_ResourceModel):
    resource_id: UUID4


class AssetModel(_ResourceModel):
    asset_id: UUID4 = Field(validation_alias="resource_id")


class ArtifactModel(_ResourceModel):
    artifact_id: UUID4 = Field(validation_alias="resource_id")


class PayloadModel(_ResourceModel):
    payload_id: UUID4
    agent_type: AgentTypeModel
    agent_template: AgentTemplateModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]
