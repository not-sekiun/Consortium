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
    datetime_modified: datetime
    md5_checksum: str | None
    is_directory: bool
