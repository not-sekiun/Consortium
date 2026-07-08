from datetime import datetime

from pydantic import UUID4, BaseModel, JsonValue

from consortium.server.models.agent_models import AgentReferenceModel
from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.user_account_models import UserAccountReferenceModel


class RepositoryResourceModel(BaseModel):
    resource_id: UUID4
    name: str | None
    description: str
    size: int | None
    extension: str | None
    exists_on_disk: bool
    datetime_created: datetime
    datetime_modified: datetime
    md5_checksum: str | None
    is_directory: bool
    data: dict[str, JsonValue]


class AssetDataModel(BaseModel):
    # `user_account` is nullable and defaults to `None` so that assets created outside
    # of the REST API (for example directly by a plugin) that do not attribute an
    # uploading user account, as well as legacy resources whose `data` field predates
    # this attribution, still validate.
    user_account: UserAccountReferenceModel | None = None


class AssetModel(RepositoryResourceModel):
    # asset_id: UUID4 = Field(validation_alias="resource_id")
    data: AssetDataModel


class ArtifactDataModel(BaseModel):
    # `agent` is nullable and defaults to `None` so that artifacts created outside of the
    # agent file manager service (for example directly by a plugin) that do not attribute
    # a producing agent, as well as legacy resources whose `data` field predates this
    # attribution, still validate.
    agent: AgentReferenceModel | None = None


class ArtifactModel(RepositoryResourceModel):
    # artifact_id: UUID4 = Field(validation_alias="resource_id")
    data: ArtifactDataModel


class PayloadModel(RepositoryResourceModel):
    payload_id: UUID4
    agent_type: AgentTypeModel
    agent_template: AgentTemplateModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]


class PayloadDataModel(BaseModel):
    agent_type: AgentTypeModel
    agent_template: AgentTemplateModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]


class PayloadModel2(RepositoryResourceModel):
    data: PayloadDataModel
