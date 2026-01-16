import datetime
import pathlib
import uuid
from typing import Any, get_type_hints

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadCreationParameterTypeError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


class _PayloadParametersModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_template: BaseAgentTemplate
    build_parameters: dict[str, JsonValue]
    resource: RepositoryFile | RepositoryDirectory
    payload_data: dict[str, JsonValue]


class Payload:
    def __init__(
        self,
        agent_template: BaseAgentTemplate,
        build_parameters: dict[str, Any],
        resource: RepositoryFile | RepositoryDirectory,
        payload_data: dict[str, Any] | None = None,
    ):
        if payload_data is None:
            payload_data = {}

        try:
            _ = _PayloadParametersModel(
                agent_template=agent_template,
                build_parameters=build_parameters,
                resource=resource,
                payload_data=payload_data,
            )
        except ValidationError as exc:
            raise PayloadCreationParameterTypeError(
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=get_type_hints(_PayloadParametersModel)[
                    exc.errors()[0]["loc"][0]
                ],
            ) from None

        self.resource = resource
        self.agent_type = agent_template.agent_type
        self.agent_template = agent_template
        self.build_parameters = build_parameters
        self.payload_data = payload_data

    @property
    def payload_id(self) -> uuid.UUID:
        return self.resource.resource_id

    @property
    def name(self) -> str:
        return self.resource.name

    @property
    def description(self) -> str:
        return self.resource.description

    @property
    def path(self) -> pathlib.Path:
        return self.resource.path

    @property
    def datetime_created(self) -> datetime.datetime:
        return self.resource.datetime_created

    @property
    def datetime_modified(self) -> datetime.datetime:
        return self.resource.datetime_modified

    @property
    def exists_on_disk(self) -> bool:
        return self.resource.exists_on_disk

    @property
    def size(self) -> int | None:
        return self.resource.size

    @property
    def is_directory(self) -> bool:
        return self.resource.is_directory

    @property
    def md5_checksum(self) -> str | None:
        if self.is_directory:
            return None
        return self.resource.md5_checksum

    def to_json(self) -> dict:
        return {
            "payload_id": str(self.payload_id),
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
            "datetime_created": self.datetime_created.isoformat(),
            "datetime_modified": self.datetime_modified.isoformat(),
            "exists_on_disk": self.exists_on_disk,
            "size": self.size,
            "md5_checksum": self.md5_checksum,
            "is_directory": self.is_directory,
            "agent_type": self.agent_type.to_json(),
            "agent_template": self.agent_template.to_json(),
            "build_parameters": self.build_parameters,
            "payload_data": self.payload_data,
        }
