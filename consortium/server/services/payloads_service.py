import json
import uuid
from collections.abc import Generator
from typing import IO, BinaryIO, Literal

import jsonschema
from loguru import logger

from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplateNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    InvalidPayloadsMetadataFileJSONError,
    InvalidPayloadsMetadataFileSchemaError,
    PayloadIDReservationNotFoundError,
    PayloadMetadataMissingError,
    PayloadNotFoundError,
    PayloadRepositoryResourceMissingError,
)
from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    RepositoryResourceNotFoundError,
)
from consortium.server.objects.payload_objects import Payload
from consortium.server.server_logging import LoggerType
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import log_and_propagate_error_on_service_method


class PayloadsService:
    def __init__(
        self,
        repository_service: RepositoryService,
        agent_templates_service: AgentTemplatesService,
    ):
        self.repository_directory_path = repository_service.repository_directory_path
        self._repository_service = repository_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._agent_templates_service = agent_templates_service
        self._payloads_metadata_file_path = (
            self._repository_service.repository_directory_path / ".payloads.json"
        )
        self._reserved_paylod_ids = set()
        self._payloads = {}
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Payloads Service"

    def __repr__(self) -> str:
        return f"PayloadsService(repository_service={self._repository_service!r})"

    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        self._repository_service.load_repository_metadata()

    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def load_payloads_metadata(self) -> None:
        payloads_metadata_json_schema = {
            "type": "object",
            "patternProperties": {
                "^[a-z0-9]+$": {
                    "type": "object",
                    "properties": {
                        "agent_template": {"type": "string"},
                        "build_parameters": {"type": "object"},
                    },
                    "required": ["agent_template", "build_parameters"],
                },
            },
        }
        if not self._payloads_metadata_file_path.exists():
            self.save_payloads_metadata()
        else:
            with self._payloads_metadata_file_path.open(mode="r") as file:
                try:
                    payloads_metadata = json.load(file)
                    jsonschema.validate(
                        payloads_metadata, payloads_metadata_json_schema
                    )
                except json.JSONDecodeError:
                    raise InvalidPayloadsMetadataFileJSONError(
                        repository_directory=str(self.repository_directory_path),
                    ) from None
                except jsonschema.ValidationError as exc:
                    raise InvalidPayloadsMetadataFileSchemaError(
                        repository_directory=str(self.repository_directory_path),
                        json_schema_error_message=str(exc),
                    ) from None
                for payload_id, payload_metadata in payloads_metadata.items():
                    try:
                        resource = self._repository_service.get_repository_resource_by_resource_id(
                            resource_id=payload_id,
                        )
                        agent_template = self._agent_templates_service.get_agent_template_by_agent_template_id(
                            agent_template_id=payload_metadata["agent_template"],
                        )
                        self._payloads[payload_id] = Payload(
                            resource=resource,
                            agent_template=agent_template,
                            build_parameters=payload_metadata["build_parameters"],
                        )
                    except RepositoryResourceNotFoundError:
                        self._logger.warning(
                            "Skipping loading payload with payload ID (resource ID) '{}' "
                            "from payloads metadata file because the corresponding "
                            "resource was not found in the payloads repository. Check "
                            "that the payload ID points to a resource in the "
                            "repository with the same resource ID.",
                            payload_id,
                        )
                        continue
                    except AgentTemplateNotFoundError:
                        self._logger.warning(
                            "Skipping loading payload with payload ID (resource ID) '{}' "
                            "from the `.payloads.json` metadata file because the "
                            "corresponding agent template '{}' was not found. Check "
                            "that the corresponding agent template is loaded.",
                            payload_id,
                        )
                        continue

    @log_and_propagate_error_on_service_method
    def save_payloads_metadata(self) -> None:
        payloads_metadata_json = {
            payload_id: {
                "agent_type": payload.agent_type.name,
                "agent_template": payload.agent_template.agent_template_id,
                "build_parameters": payload.build_parameters,
            }
            for payload_id, payload in self._payloads.items()
        }
        with self._payloads_metadata_file_path.open(mode="w") as file:
            data = json.dumps(payloads_metadata_json, indent=4)
            file.write(data)
        self._logger.debug(
            "Saved payloads metadata to {} ({} byte(s) written)",
            str(self._payloads_metadata_file_path),
            len(data),
        )

    @log_and_propagate_error_on_service_method
    def reserve_payload_id(self) -> uuid.UUID:
        payload_id = uuid.uuid4()
        self._reserved_paylod_ids.add(str(payload_id))
        self._logger.debug("Reserved payload ID '{}'", str(payload_id))
        return payload_id

    @log_and_propagate_error_on_service_method
    def create_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict,
        data: str | bytes | IO | Generator[bytes] | Generator[str],
        payload_id: str | uuid.UUID | None = None,
        is_binary: bool = True,
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        agent_template_id = str(agent_template_id)
        payload_id = str(payload_id)

        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        # Validate build parameters
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        resource = self._repository_service.create_repository_file(
            content=data,
            binary=is_binary,
            name=name,
            description=description,
        )

        # If a reserved payload ID was provided, use it and rename the generated
        # resource to that payload ID
        if payload_id is not None:
            # `_reserved_paylod_ids` contains the string representation of the reserved
            # payload IDs
            if str(payload_id) not in self._reserved_paylod_ids:
                raise PayloadIDReservationNotFoundError(
                    payload_id=payload_id,
                )
            self._reserved_paylod_ids.remove(payload_id)
            # `resource_id` expects a uuid.UUID object so if a UUID string was passed
            # instead we convert it back to a uuid.UUID object. At this point we should
            # have already confirmed that the payload ID string is a valid UUID string
            # when checking the reservation above.
            if isinstance(payload_id, str):
                payload_id = uuid.UUID(payload_id)
            resource.resource_id = payload_id
            resource.path.rename(str(payload_id))
        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
        )

        self._payloads[str(payload.payload_id)] = payload
        self.save_payloads_metadata()
        self._logger.debug(
            "Created payload file with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def create_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict,
        archive_file: bytes | Generator[bytes] | BinaryIO,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        # Validate build parameters
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        resource = self._repository_service.create_repository_directory(
            content=archive_file,
            archive_file_format=format,
            name=name,
            description=description,
        )
        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
        )
        self._payloads[str(payload.payload_id)] = payload
        self.save_payloads_metadata()
        self._logger.debug(
            "Created payload directory with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def delete_payload_by_payload_id(
        self, payload_id: str | uuid.UUID, force: bool = False
    ) -> None:
        payload_id = str(payload_id)

        payload_exists = payload_id in self._payloads
        try:
            resource_exists = (
                self._repository_service.get_repository_resource_by_resource_id(
                    resource_id=payload_id
                )
                is not None
            )
        except RepositoryResourceNotFoundError:
            resource_exists = False

        if not payload_exists and not resource_exists:
            raise PayloadNotFoundError(payload_id=payload_id)
        if payload_exists and not resource_exists:
            if not force:
                raise PayloadRepositoryResourceMissingError(payload_id=payload_id)
            self._logger.warning(
                "Payload metadata exists for payload with ID '{}', but the "
                "corresponding repository resource is missing. Proceeding due to "
                "force delete being requested",
                payload_id,
            )
        if not payload_exists and resource_exists:
            if not force:
                raise PayloadMetadataMissingError(payload_id=payload_id)
            self._logger.warning(
                "Payload repository resource exists for payload with ID '{}', but the "
                "corresponding payload metadata is missing. Proceeding due to force "
                "delete being requested",
                payload_id,
            )

        if resource_exists:
            self._repository_service.delete_repository_resource_by_resource_id(
                resource_id=payload_id
            )
        if payload_exists:
            del self._payloads[payload_id]
            self.save_payloads_metadata()
            self._logger.debug(
                "Deleted payload metadata for payload with ID '{}'", payload_id
            )

    @log_and_propagate_error_on_service_method
    def get_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> Payload:
        payload_id = str(payload_id)

        try:
            payload = self._payloads[payload_id]
            self._logger.debug(
                "Retrieved payload by payload ID '{}'",
                payload_id,
            )
            return payload
        except KeyError:
            raise PayloadNotFoundError(
                payload_id=payload_id,
            ) from None

    @log_and_propagate_error_on_service_method
    def get_all_payloads(self) -> list[Payload]:
        payloads = list(self._payloads.values())
        self._logger.debug(
            "Retrieved all payloads ({} payload(s) found)",
            len(payloads),
        )
        return payloads
