import asyncio
import pathlib
import uuid
from functools import wraps
from typing import Any, BinaryIO, Literal, TextIO

from loguru import logger
from pydantic import JsonValue

from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.event_hooks import EventType
from consortium.server.models.agent_template_models import (
    PersistentAgentTemplateReferenceModel,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.payload_objects import Payload
from consortium.server.services.agent_templates_service import AgentTemplatesService
from consortium.server.services.events_service import EventsService
from consortium.server.services.repository_service import RepositoryService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
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
        # Each payload's metadata (an immutable point-in-time reference to the generating
        # agent template, the build parameters and arbitrary payload data) is persisted in
        # the `data` field of its repository resource. The repository service writes this
        # to its `.repository.json` metadata file, so no separate payloads metadata file
        # is required. The agent template reference stores only the template's label and
        # name (not its ID, which is reissued across restarts); the `Payload` wrapper
        # resolves it to the live agent template read-time and the `data` field is
        # validated against `PayloadDataModel` at the API boundary.
        agent_template_reference = PersistentAgentTemplateReferenceModel(
            label=str(agent_template.label),
            name=agent_template.name,
        )
        return {
            "agent_template": agent_template_reference.model_dump(mode="json"),
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
    def reserve_resource_id(self) -> uuid.UUID:
        """Generates and reserves a resource ID to be claimed later during payload creation.

        Reservations are required when the caller needs to know the resource ID before
        the payload file or directory has been created (e.g., to name the file after the
        ID). The reserved ID must be provided as `resource_id` to `create_payload_file`
        or `create_payload_directory`.

        Returns:
            The reserved resource ID.
        """
        resource_id = self._repository_service.reserve_resource_id()
        self._logger.debug("Reserved resource ID '{}'", str(resource_id))
        return resource_id

    @log_and_propagate_error_on_service_method
    async def create_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: str | bytes | TextIO | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a file-based payload and associates it with an agent template.

        Build parameters are validated against the agent template before creating the
        resource. If `resource_id` is provided it must have been previously reserved via
        `reserve_resource_id`. Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            content: The file
                content to write to the repository.
            payload_data: Arbitrary metadata attached to the
                payload. When `None`, no extra metadata is stored.
            resource_id: A previously reserved ID to assign to
                this payload. When `None`, a new ID is generated automatically.
            name: A human-readable name for the payload file. When `None`,
                the resource UUID is used.
            description: An optional description for the payload.

        Returns:
            The created payload.

        Raises:
            AgentTemplateNotFoundError: If no agent template with the given ID exists.
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
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
        # Offload the blocking repository disk I/O to a worker thread so it does not
        # block the event loop, mirroring the assets and artifacts services.
        resource = await asyncio.to_thread(
            self._repository_service.create_file,
            content=content,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_payload_resource_data(
                agent_template=agent_template,
                build_parameters=build_parameters,
                payload_data=payload_data,
            ),
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {resource.resource_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Created payload file with resource ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    async def add_payload_file(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing file on disk as a file-based payload.

        Unlike `create_payload_file`, no new file is written. The file at `path`
        is moved (or copied when `copy=True`) into the repository. Build parameters
        are validated against the agent template before registration. If `resource_id`
        is provided it must have been previously reserved via `reserve_resource_id`.
        Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            path: Path to the existing file to register.
            payload_data: Arbitrary metadata attached to
                the payload. When `None`, no extra metadata is stored.
            resource_id: A previously reserved ID to
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
            ResourceIDReservationNotFoundError: If `resource_id` is provided but
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
        resource = await asyncio.to_thread(
            self._repository_service.add_file,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_payload_resource_data(
                agent_template=agent_template,
                build_parameters=build_parameters,
                payload_data=payload_data,
            ),
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {resource.resource_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Added payload file with resource ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    async def create_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        content: bytes | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        resource_id: str | uuid.UUID | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a directory-based payload by extracting an archive and associating it with an agent template.

        Build parameters are validated against the agent template before creating the
        resource. If `resource_id` is provided it must have been previously reserved via
        `reserve_resource_id`. Emits a `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            content: The archive content to
                extract into the repository directory.
            payload_data: Arbitrary metadata attached to the
                payload. When `None`, no extra metadata is stored.
            resource_id: A previously reserved ID to assign to
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
            ResourceIDReservationNotFoundError: If `resource_id` is provided but has no
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
        resource = await asyncio.to_thread(
            self._repository_service.create_directory,
            content=content,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
            resource_id=resource_id,
            data=self._build_payload_resource_data(
                agent_template=agent_template,
                build_parameters=build_parameters,
                payload_data=payload_data,
            ),
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {resource.resource_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Created payload directory with resource ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    async def add_payload_directory(
        self,
        agent_template_id: str | uuid.UUID,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        resource_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing directory on disk as a directory-based payload.

        Unlike `create_payload_directory`, no archive is extracted and no new
        directory is created. The directory at `path` is moved (or copied when
        `copy=True`) into the repository. Build parameters are validated against
        the agent template before registration. If `resource_id` is provided it
        must have been previously reserved via `reserve_resource_id`. Emits a
        `PAYLOAD_CREATED` event.

        Args:
            agent_template_id: The ID of the agent template to
                associate with the payload.
            build_parameters: Parameters used to build the agent
                generator from the template (validated against the template).
            path: Path to the existing directory to register.
            payload_data: Arbitrary metadata attached to
                the payload. When `None`, no extra metadata is stored.
            resource_id: A previously reserved ID to
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
            ResourceIDReservationNotFoundError: If `resource_id` is provided but
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
        resource = await asyncio.to_thread(
            self._repository_service.add_directory,
            path=path,
            name=name,
            description=description,
            resource_id=resource_id,
            copy=copy,
            data=self._build_payload_resource_data(
                agent_template=agent_template,
                build_parameters=build_parameters,
                payload_data=payload_data,
            ),
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_CREATED,
                message=f"Created payload: {resource.resource_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug(
            "Added payload directory with resource ID '{}'",
            resource.resource_id,
        )
        return payload

    @log_and_propagate_error_on_service_method
    async def update_payload_by_resource_id(
        self,
        resource_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        agent_template_id: str | uuid.UUID | None = None,
        build_parameters: dict[str, Any] | None = None,
        payload_data: dict[str, Any] | None = None,
    ) -> Payload:
        """Updates a payload's mutable metadata.

        `name` and `description` are updated in place when provided. The payload's stored
        `data` is only rebuilt when `agent_template_id` is passed, mirroring the parameters
        of the payload creation methods: the agent template is resolved and the supplied
        `build_parameters` are validated against it exactly as they would be on creation
        before the new metadata is recorded. When `agent_template_id` is omitted the
        existing `data` is left untouched. Emits a `PAYLOAD_UPDATED` event.

        Args:
            resource_id: The ID of the payload to update.
            name: A new human-readable name for the payload. When `None`, the existing
                name is preserved.
            description: A new description for the payload. When `None`, the existing
                description is preserved.
            agent_template_id: When provided, rebuilds the payload's `data` from this agent
                template. When omitted, the payload's existing data is left unchanged.
            build_parameters: Parameters used to build the agent generator from the
                template (validated against the template). Only used, and defaulted to an
                empty mapping, when `agent_template_id` is provided.
            payload_data: Arbitrary metadata attached to the payload. Only used when
                `agent_template_id` is provided.

        Returns:
            The updated payload.

        Raises:
            ResourceNotFoundError: If no payload with the given ID exists.
            AgentTemplateNotFoundError: If `agent_template_id` is provided but no agent
                template with that ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        data = None
        if agent_template_id is not None:
            # Validate the (possibly new) build parameters against the agent template and
            # confirm the agent template exists, exactly as the create methods do.
            agent_template = (
                self._agent_templates_service.get_agent_template_by_agent_template_id(
                    agent_template_id=agent_template_id,
                )
            )
            agent_template.create_agent_generator(
                parameters=build_parameters if build_parameters is not None else {},
            )
            data = self._build_payload_resource_data(
                agent_template=agent_template,
                build_parameters=build_parameters
                if build_parameters is not None
                else {},
                payload_data=payload_data,
            )

        resource = await asyncio.to_thread(
            self._repository_service.update_resource_by_resource_id,
            resource_id=resource_id,
            name=name,
            description=description,
            data=data,
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_UPDATED,
                message=f"Updated payload: {resource.resource_id}",
                data=payload.to_json(),
            )
        )
        self._logger.debug("Updated payload: {}", str(resource_id))
        return payload

    @log_and_propagate_error_on_service_method
    async def delete_payload_by_resource_id(self, resource_id: str | uuid.UUID) -> None:
        """Deletes a payload from disk and the repository.

        A payload is "just" a repository resource whose `data` field carries the payload
        metadata, so deleting the resource removes the payload in full. The payload's JSON
        is snapshotted before removal so it can be carried on the emitted `PAYLOAD_DELETED`
        event, then the resource is deleted from disk and deregistered.

        Args:
            resource_id: The ID of the payload to delete.

        A payload whose file or directory is already missing from the repository
        directory is deleted successfully: the record is deregistered and the event is
        still emitted.

        Raises:
            ResourceNotFoundError: If no payload with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        # Snapshot payload JSON before deletion, since to_json() reads file metadata
        # (e.g. datetime_modified) that requires the file to still exist on disk.
        resource = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        payload = Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )
        payload_json = payload.to_json()

        await asyncio.to_thread(
            self._repository_service.delete_resource_by_resource_id,
            resource_id=resource_id,
        )
        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.PAYLOAD_DELETED,
                message=f"Deleted payload: {resource_id}",
                data=payload_json,
            )
        )
        self._logger.debug("Deleted payload: {}", str(resource_id))

    @log_and_propagate_error_on_service_method
    def get_payload_by_resource_id(self, resource_id: str | uuid.UUID) -> Payload:
        """Returns a payload by its ID.

        Args:
            resource_id: The ID of the payload to retrieve.

        Returns:
            The requested payload.

        Raises:
            ResourceNotFoundError: If no payload with the given ID exists.
        """
        resource_id = normalize_uuid(resource_id)

        resource = self._repository_service.get_resource_by_resource_id(
            resource_id=resource_id
        )
        self._logger.debug(
            "Retrieved payload by resource ID '{}'",
            resource_id,
        )
        return Payload(
            resource=resource,
            agent_templates_service=self._agent_templates_service,
        )

    @log_and_propagate_error_on_service_method
    def get_all_payloads(self) -> list[Payload]:
        """Returns every payload currently tracked by the payloads service.

        Returns:
            A list of all payloads, covering both file and directory payloads, each
                wrapping its repository resource. Empty if no payloads exist.
        """
        payloads = self._repository_service.get_all_resources()
        self._logger.debug(
            "Retrieved all payloads ({} payload(s) found)",
            len(payloads),
        )
        return [
            Payload(
                resource=payload,
                agent_templates_service=self._agent_templates_service,
            )
            for payload in payloads
        ]
