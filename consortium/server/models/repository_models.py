from datetime import datetime

from pydantic import UUID4, BaseModel, JsonValue

from consortium.server.models.agent_models import AgentModel, AgentReferenceModel
from consortium.server.models.agent_template_models import (
    AgentTemplateModel,
    PersistentAgentTemplateReferenceModel,
)
from consortium.server.models.user_account_models import (
    LiveUserAccountReferenceModel,
    PersistentUserAccountReferenceModel,
)


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


# This data model is what is actually stored on disk in the asset services
# .repository.json
class PersistentAssetDataModel(BaseModel):
    # `user_account` holds the immutable point-in-time reference recorded at upload. It
    # is nullable and defaults to `None` so that assets created outside of the REST API
    # (for example directly by a plugin) that do not attribute an uploading account, as
    # well as legacy resources whose `data` field predates this attribution, still
    # validate.
    user_account: PersistentUserAccountReferenceModel | None = None


# This data model is what is resolved at runtime by the asset service
class ResolvedAssetDataModel(PersistentAssetDataModel):
    # `resolved_user_account` is the live, read-time resolution of `user_account` added
    # by the `Asset` wrapper's `to_json`. It is never persisted (the repository stores
    # only the reference above) and is `None` when the uploading account cannot be
    # resolved (no attribution, or the account was deleted after upload).
    resolved_user_account: LiveUserAccountReferenceModel | None = None


class AssetModel(RepositoryResourceModel):
    data: ResolvedAssetDataModel


# This data model is what is actually stored on disk in the artifacts services
# .repository.json
class PersistentArtifactDataModel(BaseModel):
    # `agent` holds the immutable point-in-time reference recorded at creation. It is
    # nullable and defaults to `None` so that artifacts created outside of the agent file
    # manager service (for example directly by a plugin) that do not attribute a
    # producing agent, as well as legacy resources whose `data` field predates this
    # attribution, still validate.
    agent: AgentReferenceModel | None = None


# This data model is what is resolved at runtime by the artifact service
class ResolvedArtifactDataModel(PersistentArtifactDataModel):
    # `resolved_agent` is the live, read-time resolution of `agent` added by the
    # `Artifact` wrapper's `to_json`. It is never persisted (the repository stores only
    # the reference above) and is `None` when the producing agent cannot be resolved (no
    # attribution, or the agent was deleted after creation).
    resolved_agent: AgentModel | None = None


class ArtifactModel(RepositoryResourceModel):
    data: ResolvedArtifactDataModel


# This data model is what is actually stored on disk in the artifacts services
# .repository.json
class PersistentPayloadDataModel(BaseModel):
    agent_template: PersistentAgentTemplateReferenceModel
    build_parameters: dict[str, JsonValue]
    payload_data: dict[str, JsonValue]


# This data model is what is resolved at runtime by the payloads service
class ResolvedPayloadDataModel(PersistentPayloadDataModel):
    resolved_agent_template: AgentTemplateModel | None


class PayloadModel(RepositoryResourceModel):
    data: ResolvedPayloadDataModel
