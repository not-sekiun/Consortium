from pydantic import BaseModel

from consortium.server.objects.user_account_objects import UserRole


class NewUserAccountRequestBodyModel(BaseModel):
    username: str
    password: str
    role: UserRole


class NewPasswordRequestBodyModel(BaseModel):
    password: str


class NewRoleRequestBodyModel(BaseModel):
    role: UserRole
