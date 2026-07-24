from typing import Any, Literal

from fastapi import UploadFile
from pydantic import BaseModel, JsonValue


class AgentTaskRequestBodyModel(BaseModel):
    command: str
    arguments: dict[str, Any] | list[Any]


class CreateUserAccountRequestBodyModel(BaseModel):
    username: str
    password: str
    role: str


class UpdateAgentRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None


class UpdateAgentGeneratorRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None


class UpdateListenerRequestBodyModel(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, JsonValue] | None = None


class UpdateDisplayNameRequestBodyModel(BaseModel):
    display_name: str


class UploadAssetRequestBodyModel(BaseModel):
    file: UploadFile
    is_directory: bool
    name: str | None = None
    description: str | None = None
    directory_archive_file_format: (
        Literal[".zip", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz"] | None
    ) = None
