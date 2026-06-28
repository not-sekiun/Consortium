import uuid

from pydantic import UUID4, BaseModel, Field


class UserAccountModel(BaseModel):
    user_account_id: UUID4 = Field(default_factory=uuid.uuid4)
    username: str
    password: str
    role: str

    def __str__(self) -> str:
        return f"'{self.username}' ({self.user_account_id})"
