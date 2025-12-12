from pydantic import BaseModel

from consortium.server.objects.user_account_objects import UserRole


class PasswordUpdateRequestDataModel(BaseModel):
    old_password: str
    new_password: str


class UpdateOwnUserAccountRequestDataModel(BaseModel):
    username: str | None = None
    password: PasswordUpdateRequestDataModel | None = None


class UpdateUserAccountByUserAccountIDRequestDataModel(BaseModel):
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None
