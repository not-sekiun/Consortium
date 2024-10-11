from pydantic import BaseModel

from consortium.server.objects.user_account_objects import UserRole


class _PasswordUpdateRequestDataModel(BaseModel):
    old_password: str
    new_password: str


class UpdateOwnUserAccountRequestDataModel(BaseModel):
    username: str | None = None
    password: _PasswordUpdateRequestDataModel | None = None


class UpdateUserAccountByUserAccountIDRequestDataModel(BaseModel):
    username: str | None = None
    password: _PasswordUpdateRequestDataModel | None = None
    role: UserRole | None = None
