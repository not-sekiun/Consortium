import uuid
from datetime import datetime

from pydantic import BaseModel


class RepositoryResourceModel(BaseModel):
    resource_id: uuid.UUID
    name: str | None
    description: str
    size: int | None
    exists_on_disk: bool
    datetime_created: datetime
    datetime_updated: datetime
    is_directory: bool


class RepositoryFileModel(RepositoryResourceModel):
    md5_checksum: str | None
    is_directory: bool = False


class RepositoryDirectoryModel(RepositoryResourceModel):
    is_directory: bool = True
