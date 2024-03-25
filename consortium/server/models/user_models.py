from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from consortium.server.objects.user_account_objects import UserRole


class JSONWebTokenModel(BaseModel):
    access_token: str
    token_type: str


class UserModel(BaseModel):
    username: str
    password: str
    role: UserRole
    json_web_token: JSONWebTokenModel
    remote_host: str
    datetime_connected: datetime = Field(default_factory=datetime.now)
    user_id: UUID = Field(default_factory=uuid4)
