import uuid

from pydantic import UUID4, BaseModel, ConfigDict, Field, RootModel


class UserAccountModel(BaseModel):
    user_account_id: UUID4 = Field(default_factory=uuid.uuid4)
    username: str
    password: str
    role: str

    def __str__(self) -> str:
        return f"'{self.username}' ({self.user_account_id})"


# The on-disk form of a single user account entry in the user accounts file. Kept separate
# from `UserAccountModel` because the two describe different things: `user_account_id` is
# reissued on every load and so is deliberately not accepted from the file, and the
# non-empty constraints below are what the file has to satisfy before an account can be
# constructed at all. `extra="forbid"` means a misspelled key is reported against the file
# rather than silently dropped, which is the failure the previous JSON schema allowed
# through.
class PersistentUserAccountModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: str


# Covers the whole user accounts file in one validation pass: the top level array, every
# entry in it, and the non-empty constraints on each field. Anything malformed surfaces as
# a single `ValidationError` the service converts into `UserAccountsFileSchemaError`,
# rather than escaping later as a raw `pydantic.ValidationError` while the accounts are
# being constructed. Role values are not checked here: valid roles come from the
# authorization service at runtime, so the service validates them in a second pass.
class PersistentUserAccountsFileModel(RootModel[list[PersistentUserAccountModel]]):
    root: list[PersistentUserAccountModel]


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
