import asyncio
import pathlib
import uuid
from functools import wraps
from typing import Any, BinaryIO, Literal, TextIO

from loguru import logger
from pydantic import JsonValue

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.event_hooks import EventType
from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplateNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions import (
    PayloadIDReservationNotFoundError,
    PayloadNotFoundError,
)
from consortium.server.exceptions.consortium_exceptions.repository_consortium_exceptions import (
    RepositoryResourceNotFoundError,
    ResourceIDReservationNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.payload_objects import Payload
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
        # self._payloads = {}
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Payloads Service"

    def __repr__(self) -> str:
        return f"PayloadsService(repository_service={self._repository_service!r})"

    @staticmethod
    def _build_payload_resource_data(
        agent_template: BaseAgentTemplate,
        build_parameters: dict[str, JsonValue],
        payload_data: dict[str, JsonValue] | None,
    ) -> dict[str, JsonValue]:
        # Each payload's metadata (the agent template label, build parameters and
        # arbitrary payload data) is persisted in the `data` field of its repository
        # resource. The repository service writes this to its `.repository.json`
        # metadata file, so no separate payloads metadata file is required.
        return {
            "agent_template": str(agent_template.label),
            "build_parameters": build_parameters,
            "payload_data": payload_data if payload_data is not None else {},
        }

    # @wraps copies function docstring information over to avoid rewriting it, used for
    # boilerplate forwarding methods that don't do anything meaningfully different. We
    # still need to include some docstring pointing to the forwarded method since
    # mkdocstrings' griffe analyzer only does static analysis when generating
    # documentation
    @wraps(RepositoryService.load_repository_metadata)
    @log_and_propagate_error_on_service_method
    def load_repository_metadata(self) -> None:
        """See [`RepositoryService.load_repository_metadata`][consortium.server.services.repository_service.RepositoryService.load_repository_metadata]."""
        self._repository_service.load_repository_metadata()
        self._logger.debug("Loaded payloads repository metadata")

    @wraps(RepositoryService.save_repository_metadata)
    @log_and_propagate_error_on_service_method
    def save_repository_metadata(self) -> None:
        """See [`RepositoryService.save_repository_metadata`][consortium.server.services.repository_service.RepositoryService.save_repository_metadata]."""
        self._repository_service.save_repository_metadata()

    @log_and_propagate_error_on_service_method
    def load_payloads_metadata(self) -> None:
        """Reconstructs in-memory payloads from the repository resource metadata.

        Each payload's metadata (agent template label, build parameters and payload
        data) is stored in the `data` field of its repository resource, which the
        repository service persists in its `.repository.json` metadata file. This method
        iterates over the resources tracked by the repository service and rebuilds the
        corresponding payloads. Resources whose `data` field is missing the expected
        payload fields, or whose agent template cannot be found, are logged as warnings
        and skipped.

        Note that `self.load_repository_metadata` must be called before this method or
        else the repository resources (and their `data` fields) will not be available to
        reconstruct payloads from.
        """
        resources = self._repository_service.get_all_resources()
        loaded_count = 0
        skipped_count = 0
        for resource in resources:
            payload_id = str(resource.resource_id)
            try:
                agent_template_label = resource.data["agent_template"]
                build_parameters = resource.data["build_parameters"]
                payload_data = resource.data["payload_data"]
            except KeyError, TypeError:
                self._logger.warning(
                    "Skipping loading payload with payload ID (resource ID) '{}' "
                    "because its repository resource metadata is missing the expected "
                    "payload fields ('{}', '{}', '{}') in its `data` field.",
                    payload_id,
                    "agent_template",
                    "build_parameters",
                    "payload_data",
                )
                skipped_count += 1
                continue
            try:
                agent_template = (
                    self._agent_templates_service.get_agent_template_by_label(
                        label=agent_template_label,
                    )
                )
            except AgentTemplateNotFoundError:
                self._logger.warning(
                    "Skipping loading payload with payload ID (resource ID) '{}' "
                    "because the corresponding agent template '{}' was not found. Check "
                    "that the corresponding agent template is loaded.",
                    payload_id,
                    agent_template_label,
                )
                skipped_count += 1
                continue
            self._payloads[payload_id] = Payload(
                resource=resource,
                agent_template=agent_template,
                build_parameters=build_parameters,
                payload_data=payload_data,
            )
            loaded_count += 1
        if resources and loaded_count == 0:
            self._logger.error(
                "Failed to load any payloads from the repository metadata "
                "({} resource(s) found, all skipped). This may indicate that the "
                "repository service or agent templates have not been loaded yet, or "
                "that the repository metadata is fully stale.",
                len(resources),
            )
        elif skipped_count > 0:
            self._logger.warning(
                "Loaded {}/{} payload(s) from the repository metadata "
                "({} skipped due to missing payload metadata or agent templates).",
                loaded_count,
                loaded_count + skipped_count,
                skipped_count,
            )

    @log_and_propagate_error_on_service_method
    def reserve_payload_id(self) -> uuid.UUID:
        """Generates and reserves a payload ID to be claimed later during payload creation.

        Reservations are required when the caller needs to know the payload ID before
        the payload file or directory has been created (e.g., to name the file after the
        ID). The reserved ID must be provided as `payload_id` to `create_payload_file`
        or `create_payload_directory`.

        Returns:
            The reserved payload ID.
        """
        payload_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved payload ID '{}'", str(payload_id))
        return payload_id

    @log_and_propagate_error_on_service_method
    def create_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: str | bytes | TextIO | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a file-based payload and associates it with an agent template.

        Build parameters are validated against the agent template before creating the
        resource. If `payload_id` is provided it must have been previously reserved via
        `reserve_payload_id`. Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            content: The file
                content to write to the repository.
            payload_data: Arbitrary metadata attached to the
                payload. When `None`, no extra metadata is stored.
            payload_id: A previously reserved ID to assign to
                this payload. When `None`, a new ID is generated automatically.
            name: A human-readable name for the payload file. When `None`,
                the resource UUID is used.
            description: An optional description for the payload.

        Returns:
            The created payload.

        Raises:
            AgentTemplateNotFoundError: If no agent template with the given ID exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
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
        try:
            resource = self._repository_service.create_file(
                content=content,
                name=name,
                description=description,
                resource_id=payload_id,
                data=self._build_payload_resource_data(
                    agent_template=agent_template,
                    build_parameters=build_parameters,
                    payload_data=payload_data,
                ),
            )
        except ResourceIDReservationNotFoundError:
            raise PayloadIDReservationNotFoundError(
                payload_id=normalize_uuid(payload_id),
            ) from None

        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )
        self._payloads[str(payload.payload_id)] = payload

        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {payload.payload_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Created payload file with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def add_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing file on disk as a file-based payload.

        Unlike `create_payload_file`, no new file is written. The file at `path`
        is moved (or copied when `copy=True`) into the repository. Build parameters
        are validated against the agent template before registration. If `payload_id`
        is provided it must have been previously reserved via `reserve_payload_id`.
        Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            path: Path to the existing file to register.
            payload_data: Arbitrary metadata attached to
                the payload. When `None`, no extra metadata is stored.
            payload_id: A previously reserved ID to
                assign to this payload. When `None`, a new ID is generated.
            name: A human-readable name for the payload file. When
                `None`, the original filename is used.
            description: An optional description for the payload.
            copy: When `False` (default) the source file is moved into the
                repository. When `True` the source file is copied and the original
                is left in place.

        Returns:
            The registered payload.

        Raises:
            AgentTemplateNotFoundError: If no agent template with the given ID
                exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but
                has no corresponding reservation.
        """
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        try:
            resource = self._repository_service.add_file(
                path=path,
                name=name,
                description=description,
                resource_id=payload_id,
                copy=copy,
                data=self._build_payload_resource_data(
                    agent_template=agent_template,
                    build_parameters=build_parameters,
                    payload_data=payload_data,
                ),
            )
        except ResourceIDReservationNotFoundError:
            raise PayloadIDReservationNotFoundError(
                payload_id=normalize_uuid(payload_id),
            ) from None

        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )
        self._payloads[str(payload.payload_id)] = payload

        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {payload.payload_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Added payload file with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def create_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: bytes | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a directory-based payload by extracting an archive and associating it with an agent template.

        Build parameters are validated against the agent template before creating the
        resource. If `payload_id` is provided it must have been previously reserved via
        `reserve_payload_id`. Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            content: The archive content to
                extract into the repository directory.
            payload_data: Arbitrary metadata attached to the
                payload. When `None`, no extra metadata is stored.
            payload_id: A previously reserved ID to assign to
                this payload. When `None`, a new ID is generated automatically.
            archive_file_format: The
                format of the archive to extract. Defaults to `"zip"`.
            name: A human-readable name for the payload directory. When
                `None`, the resource UUID is used.
            description: An optional description for the payload.

        Returns:
            The created payload.

        Raises:
            AgentTemplateNotFoundError: If no agent template with the given ID exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
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
        try:
            resource = self._repository_service.create_directory(
                content=content,
                archive_file_format=archive_file_format,
                name=name,
                description=description,
                resource_id=payload_id,
                data=self._build_payload_resource_data(
                    agent_template=agent_template,
                    build_parameters=build_parameters,
                    payload_data=payload_data,
                ),
            )
        except ResourceIDReservationNotFoundError:
            raise PayloadIDReservationNotFoundError(
                payload_id=normalize_uuid(payload_id),
            ) from None

        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )
        self._payloads[str(payload.payload_id)] = payload
        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {payload.payload_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Created payload directory with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def add_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing directory on disk as a directory-based payload.

        Unlike `create_payload_directory`, no archive is extracted and no new
        directory is created. The directory at `path` is moved (or copied when
        `copy=True`) into the repository. Build parameters are validated against
        the agent template before registration. If `payload_id` is provided it
        must have been previously reserved via `reserve_payload_id`. Emits a
        `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            path: Path to the existing directory to register.
            payload_data: Arbitrary metadata attached to
                the payload. When `None`, no extra metadata is stored.
            payload_id: A previously reserved ID to
                assign to this payload. When `None`, a new ID is generated.
            name: A human-readable name for the payload directory.
                When `None`, the original directory name is used.
            description: An optional description for the payload.
            copy: When `False` (default) the source directory is moved into
                the repository. When `True` the source directory is copied and the
                original is left in place.

        Returns:
            The registered payload.

        Raises:
            AgentTemplateNotFoundError: If no agent template with the given ID
                exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but
                has no corresponding reservation.
        """
        agent_template = (
            self._agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
        agent_template.create_agent_generator(
            parameters=build_parameters,
        )
        try:
            resource = self._repository_service.add_directory(
                path=path,
                name=name,
                description=description,
                resource_id=payload_id,
                copy=copy,
                data=self._build_payload_resource_data(
                    agent_template=agent_template,
                    build_parameters=build_parameters,
                    payload_data=payload_data,
                ),
            )
        except ResourceIDReservationNotFoundError:
            raise PayloadIDReservationNotFoundError(
                payload_id=normalize_uuid(payload_id),
            ) from None

        payload = Payload(
            resource=resource,
            agent_template=agent_template,
            build_parameters=build_parameters,
            payload_data=payload_data,
        )
        self._payloads[str(payload.payload_id)] = payload

        asyncio.create_task(
            self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {payload.payload_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Added payload directory with payload ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    def delete_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> None:
        """Deletes a payload's repository resource and its associated metadata.

        A `PAYLOAD_DELETED` event is only emitted when both the metadata and the
        repository resource existed prior to deletion. If only one side exists, a
        warning is logged and the orphaned side is cleaned up without emitting an event.

        Args:
            payload_id: The ID of the payload to delete.

        Raises:
            PayloadNotFoundError: If neither payload metadata nor a matching repository
                resource exists.
        """
        payload_id = normalize_uuid(payload_id)

        payload_exists = payload_id in self._payloads
        try:
            resource_exists = (
                self._repository_service.get_resource_by_resource_id(
                    resource_id=payload_id
                )
                is not None
            )
        except RepositoryResourceNotFoundError:
            resource_exists = False

        if not payload_exists and not resource_exists:
            raise PayloadNotFoundError(payload_id=payload_id)
        if payload_exists and not resource_exists:
            self._logger.warning(
                "Payload metadata exists for payload with ID '{}', but the "
                "corresponding repository resource is missing. Cleaning up orphaned "
                "metadata.",
                payload_id,
            )
        if not payload_exists and resource_exists:
            self._logger.warning(
                "Payload repository resource exists for payload with ID '{}', but the "
                "corresponding payload metadata is missing. Cleaning up orphaned "
                "resource.",
                payload_id,
            )

        # Snapshot payload JSON before deleting the resource and payload metadata,
        # since to_json() reads file metadata (e.g. datetime_modified) that requires
        # the file to exist on disk. However if either the payload metadata or the
        # repository resource is missing, we skip since the payload deletion even will
        # not be fired
        payload_json = (
            self._payloads[payload_id].to_json()
            if payload_exists and resource_exists
            else None
        )

        if resource_exists:
            self._repository_service.delete_resource_by_resource_id(
                resource_id=payload_id
            )
        if payload_exists:
            # The payload metadata lives in the resource's `data` field, so deleting the
            # repository resource above already removed it from the repository metadata
            # file. Here we only need to drop the in-memory payload entry.
            self._payloads.pop(payload_id)
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
                        event_type=EventType.PAYLOAD_DELETED,
                        message=f"Deleted payload: {payload_id}",
                        data=payload_json,
                    )
                )

    @log_and_propagate_error_on_service_method
    def get_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> Payload:
        """Returns a payload by its ID.

        Args:
            payload_id: The ID of the payload to retrieve.

        Returns:
            The requested payload.

        Raises:
            PayloadNotFoundError: If no payload with the given ID exists.
        """
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
        """Returns all currently loaded payloads.

        Returns:
            A list of all payloads. Empty if none have been created.
        """
        payloads = list(self._payloads.values())
        self._logger.debug(
            "Retrieved all payloads ({} payload(s) found)",
            len(payloads),
        )
        return payloads
