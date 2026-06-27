from datetime import datetime

from pydantic import UUID4, BaseModel


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
