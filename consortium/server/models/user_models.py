import uuid
from datetime import datetime

from pydantic import UUID4, BaseModel, Field

from consortium.server.utils import utc_now


class UserAccountReferenceModel(BaseModel):
    user_account_id: UUID4
    username: str


class UserModel(BaseModel):
    user_id: UUID4 = Field(default_factory=uuid.uuid4, examples=["string"])
    username: str
    display_name: str
    role: str = Field(examples=["string"])
    user_account: UserAccountReferenceModel
    datetime_connected: datetime = Field(
        default_factory=utc_now,
        examples=["string"],
    )
    datetime_last_active: datetime = Field(
        default_factory=utc_now,
        examples=["string"],
    )


class JSONWebTokenModel(BaseModel):
    access_token: str
    token_type: str
