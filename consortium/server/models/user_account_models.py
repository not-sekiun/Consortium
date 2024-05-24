import uuid

from pydantic import BaseModel, Field

from consortium.server.objects.user_account_objects import UserRole


class UserAccountModel(BaseModel):
    user_account_id: uuid.UUID = Field(default_factory=uuid.uuid4, examples=["string"])
    username: str
    password: str
    role: UserRole = Field(examples=["string"])

    def __str__(self) -> str:
        return f"'{self.username}' ({self.user_account_id})"
