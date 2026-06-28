from pydantic import BaseModel


class PasswordUpdateRequestDataModel(BaseModel):
    old_password: str
    new_password: str


class UpdateOwnUserAccountRequestDataModel(BaseModel):
    username: str | None = None
    password: PasswordUpdateRequestDataModel | None = None


class UpdateUserAccountByUserAccountIDRequestDataModel(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None
