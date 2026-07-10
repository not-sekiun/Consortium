import uuid

from pydantic import UUID4, BaseModel, Field


class UserAccountModel(BaseModel):
    user_account_id: UUID4 = Field(default_factory=uuid.uuid4)
    username: str
    password: str
    role: str

    def __str__(self) -> str:
        return f"'{self.username}' ({self.user_account_id})"


class LiveUserAccountReferenceModel(BaseModel):
    user_account_id: UUID4
    username: str
    role: str


# Used by assets to store persistent references on disk to the user account that
# uploaded them. Omits `user_account_id` because that can vary on restart (user accounts
# currently live in memory, so every restart reissues IDs). `username` is the persistent
# identifier for a user account regardless of its ID, and `role` records the account's
# role as of the moment the asset was uploaded.
class PersistentUserAccountReferenceModel(BaseModel):
    username: str
    role: str
