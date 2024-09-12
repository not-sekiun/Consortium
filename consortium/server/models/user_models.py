import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from consortium.server.objects.user_account_objects import UserRole


class UserAccountReferenceModel(BaseModel):
    user_account_id: uuid.UUID
    username: str


class UserModel(BaseModel):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, examples=["string"])
    username: str
    display_name: str
    role: UserRole = Field(examples=["string"])
    user_account: UserAccountReferenceModel
    datetime_connected: datetime = Field(
        default_factory=datetime.now,
        examples=["string"],
    )
    datetime_last_active: datetime = Field(
        default_factory=datetime.now,
        examples=["string"],
    )


class JSONWebTokenModel(BaseModel):
    access_token: str
    token_type: str
