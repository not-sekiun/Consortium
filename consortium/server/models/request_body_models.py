from typing import Any

from pydantic import BaseModel, Field

from consortium.server.objects.user_account_objects import UserRole


class NewUserAccountRequestBodyModel(BaseModel):
    username: str
    password: str
    role: UserRole


class NewUserAccountAttributesRequestBodyModel(BaseModel):
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None


class NewListenerAttributesRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


class NewAgentGeneratorAttributesRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


class AgentTaskRequestBodyModel(BaseModel):
    command: str
    arguments: dict[str, Any] = Field(default_factory=dict)
