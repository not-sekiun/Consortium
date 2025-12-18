import datetime
import pathlib
import uuid

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


class Payload:
    def __init__(
        self,
        agent_template: BaseAgentTemplate,
        build_parameters: dict,
        resource: RepositoryFile | RepositoryDirectory,
    ):
        self.resource = resource
        self.agent_type = agent_template.agent_type
        self.agent_template = agent_template
        self.build_parameters = build_parameters

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
        }
