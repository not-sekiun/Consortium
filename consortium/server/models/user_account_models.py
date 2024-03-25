import uuid

from pydantic import BaseModel, Field

from consortium.server.objects.user_account_objects import UserRole


class UserAccountModel(BaseModel):
    user_account_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    username: str
    password: str
    role: UserRole
