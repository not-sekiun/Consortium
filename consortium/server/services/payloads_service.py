import asyncio
import json
import uuid
from collections.abc import Generator
from typing import IO, Any, BinaryIO, Literal

import jsonschema
from loguru import logger

from consortium.framework.event_hooks import EventType
from consortium.framework.event_hooks._event import Event
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
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class PayloadsService:
    def __init__(
        self,
        events_service: EventsService,
        repository_service: RepositoryService,
        agent_templates_service: AgentTemplatesService,
    ):
        self._events_service = events_service
        self._repository_service = repository_service
        self._agent_templates_service = agent_templates_service
        self.repository_directory_path = repository_service.repository_directory_path
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._payloads_metadata_file_path = (
            self._repository_service.repository_directory_path / ".payloads.json"
        )
        self._reserved_payload_ids = set()
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
                        "payload_data": {"type": "object"},
                    },
                    "required": ["agent_template", "build_parameters", "payload_data"],
                    "additionalProperties": False,
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
                            payload_data=payload_metadata["payload_data"],
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
                "payload_data": payload.payload_data,
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
        self._reserved_payload_ids.add(str(payload_id))
        self._logger.debug("Reserved payload ID '{}'", str(payload_id))
        return payload_id

    @log_and_propagate_error_on_service_method
    def create_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: str | bytes | IO | Generator[bytes] | Generator[str],
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        is_binary: bool = True,
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        # Validate payload build parameters against the agent template and check that
        # the agent template exists
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        resource = self._repository_service.create_repository_file(
            content=content,
            binary=is_binary,
            name=name,
            description=description,
        )

        # If a reserved payload ID was provided, use it and rename the generated
        # resource to that payload ID
        if payload_id is not None:
            payload_id = normalize_uuid(payload_id)
            # `_reserved_payload_ids` contains the string representation of the reserved
            # payload IDs
            if payload_id not in self._reserved_payload_ids:
                raise PayloadIDReservationNotFoundError(
                    payload_id=payload_id,
                )
            self._reserved_payload_ids.remove(payload_id)
            # `resource_id` expects a uuid.UUID object so if a UUID string was passed
            # instead we convert it back to a uuid.UUID object. At this point we should
            # have already confirmed that the payload ID string is a valid UUID string
            # when checking the reservation above.
            resource.resource_id = uuid.UUID(payload_id)
            resource.path.rename(payload_id)

        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )
        self._payloads[str(payload.payload_id)] = payload
        self.save_payloads_metadata()

        asyncio.create_task(
            self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.PAYLOAD_CREATED,
                    data=payload.to_json(),
                )
            )
        )
        self._logger.debug(
            "Created payload file with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def create_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: bytes | Generator[bytes] | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        # Validate payload build parameters against the agent template and check that
        # the agent template exists
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        resource = self._repository_service.create_repository_directory(
            content=content,
            archive_file_format=format,
            name=name,
            description=description,
        )

        # If a reserved payload ID was provided, use it and rename the generated
        # resource to that payload ID
        if payload_id is not None:
            payload_id = normalize_uuid(payload_id)
            # `_reserved_payload_ids` contains the string representation of the reserved
            # payload IDs
            if payload_id not in self._reserved_payload_ids:
                raise PayloadIDReservationNotFoundError(
                    payload_id=payload_id,
                )
            self._reserved_payload_ids.remove(payload_id)
            # `resource_id` expects a uuid.UUID object so if a UUID string was passed
            # instead we convert it back to a uuid.UUID object. At this point we should
            # have already confirmed that the payload ID string is a valid UUID string
            # when checking the reservation above.
            resource.resource_id = uuid.UUID(payload_id)
            resource.path.rename(payload_id)
        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )

        self._payloads[str(payload.payload_id)] = payload
        self.save_payloads_metadata()
        asyncio.create_task(
            self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.PAYLOAD_CREATED,
                    data=payload.to_json(),
                )
            )
        )
        self._logger.debug(
            "Created payload directory with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def delete_payload_by_payload_id(
        self, payload_id: str | uuid.UUID, force: bool = False
    ) -> None:
        payload_id = normalize_uuid(payload_id)

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
            payload = self._payloads.pop(payload_id)
            self.save_payloads_metadata()
            self._logger.debug(
                "Deleted payload metadata for payload with ID '{}'", payload_id
            )
            # Only trigger a PAYLOAD_DELETED event if both the payload metadata and the
            # repository resource existed prior to deletion. If the payload metadata does
            # not exist and the repository resource does, or vice versa, we skip triggering
            # the event and treat it as an orphaned resource/metadata deletion.
            if resource_exists:
                asyncio.create_task(
                    self._events_service.trigger_event(
                        event=Event(
                            event_type=EventType.PAYLOAD_DELETED,
                            data=payload.to_json(),
                        )
                    )
                )

    @log_and_propagate_error_on_service_method
    def get_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> Payload:
        payload_id = normalize_uuid(payload_id)

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
