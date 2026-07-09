import pathlib
import uuid
from collections.abc import Generator
from functools import wraps
from typing import IO, Any, BinaryIO, Literal

from loguru import logger

from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.payload_objects import Payload
from consortium.server.services.payloads_service import PayloadsService
from consortium.server.utils import log_and_propagate_error_on_service_method


class AgentTemplatesPayloadsService:
    def __init__(
        self,
        agent_template_id: str | uuid.UUID,
    ):
        # Importing here to avoid circular imports.
        import consortium.server.server_singletons as server_singletons

        self._payloads_service = server_singletons.payloads_service
        self._agent_template_id = agent_template_id
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Agent Templates Payload Service"

    def __repr__(self) -> str:
        return (
            f"AgentTemplatesPayloadsService("
            f"payloads_service={self._payloads_service!r}, "
            f"agent_template_id={self._agent_template_id!r}"
            f")"
        )

    # @wraps copies function docstring information over to avoid rewriting it, used for
    # boilerplate forwarding methods that don't do anything meaningfully different. We
    # still need to include some docstring pointing to the forwarded method since
    # mkdocstrings' griffe analyzer only does static analysis when generating
    # documentation
    @wraps(PayloadsService.reserve_payload_id)
    @log_and_propagate_error_on_service_method
    def reserve_payload_id(self) -> uuid.UUID:
        """See `PayloadsService.reserve_payload_id`."""
        return self._payloads_service.reserve_payload_id()

    @log_and_propagate_error_on_service_method
    def create_payload_file(
        self,
        build_parameters: dict[str, Any],
        content: str | bytes | IO | Generator[bytes] | Generator[str],
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a file-based payload associated with the bound agent template.

        Forwards to `PayloadsService.create_payload_file`, injecting the agent template
        ID bound to this service so the caller does not need to supply it.

        Args:
            build_parameters: Parameters used to build the agent generator from the
                bound agent template (validated against the template).
            content: The file content to write to the repository.
            payload_data: Arbitrary metadata attached to the payload. When `None`, no
                extra metadata is stored.
            payload_id: A previously reserved ID to assign to this payload. When
                `None`, a new ID is generated automatically.
            name: A human-readable name for the payload file. When `None`, the
                resource UUID is used.
            description: An optional description for the payload.

        Returns:
            The created payload.

        Raises:
            AgentTemplateNotFoundError: If the bound agent template ID no longer exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
        return self._payloads_service.create_payload_file(
            agent_template_id=self._agent_template_id,
            build_parameters=build_parameters,
            content=content,
            payload_data=payload_data,
            payload_id=payload_id,
            name=name,
            description=description,
        )

    @log_and_propagate_error_on_service_method
    def create_payload_directory(
        self,
        build_parameters: dict[str, Any],
        content: bytes | Generator[bytes] | BinaryIO,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        archive_file_format: Literal["zip", "tar", "gztar", "bztar", "xztar"] = "zip",
        name: str | None = None,
        description: str = "",
    ) -> Payload:
        """Creates a directory-based payload associated with the bound agent template.

        Forwards to `PayloadsService.create_payload_directory`, injecting the agent
        template ID bound to this service so the caller does not need to supply it.

        Args:
            build_parameters: Parameters used to build the agent generator from the
                bound agent template (validated against the template).
            content: The archive content to extract into the repository directory.
            payload_data: Arbitrary metadata attached to the payload. When `None`, no
                extra metadata is stored.
            payload_id: A previously reserved ID to assign to this payload. When
                `None`, a new ID is generated automatically.
            archive_file_format: The format of the archive to extract. Defaults to
                `"zip"`.
            name: A human-readable name for the payload directory. When `None`, the
                resource UUID is used.
            description: An optional description for the payload.

        Returns:
            The created payload.

        Raises:
            AgentTemplateNotFoundError: If the bound agent template ID no longer exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
        return self._payloads_service.create_payload_directory(
            agent_template_id=self._agent_template_id,
            build_parameters=build_parameters,
            content=content,
            payload_data=payload_data,
            payload_id=payload_id,
            archive_file_format=archive_file_format,
            name=name,
            description=description,
        )

    @log_and_propagate_error_on_service_method
    def add_payload_file(
        self,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing file on disk as a payload for the bound agent template.

        Forwards to `PayloadsService.add_payload_file`, injecting the agent template
        ID bound to this service so the caller does not need to supply it.

        Args:
            build_parameters: Parameters used to build the agent generator from the
                bound agent template (validated against the template).
            path: Path to the existing file to register.
            payload_data: Arbitrary metadata attached to the payload. When `None`,
                no extra metadata is stored.
            payload_id: A previously reserved ID to assign to this payload. When
                `None`, a new ID is generated.
            name: A human-readable name for the payload file. When `None`, the
                original filename is used.
            description: An optional description for the payload.
            copy: When `False` (default) the source file is moved into the repository.
                When `True` the source file is copied and the original is left in
                place.

        Returns:
            The registered payload.

        Raises:
            AgentTemplateNotFoundError: If the bound agent template ID no longer exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
        return self._payloads_service.add_payload_file(
            agent_template_id=self._agent_template_id,
            build_parameters=build_parameters,
            path=path,
            payload_data=payload_data,
            payload_id=payload_id,
            name=name,
            description=description,
            copy=copy,
        )

    @log_and_propagate_error_on_service_method
    def add_payload_directory(
        self,
        build_parameters: dict[str, Any],
        path: pathlib.Path | str,
        payload_data: dict[str, Any] | None = None,
        payload_id: str | uuid.UUID | None = None,
        name: str | None = None,
        description: str = "",
        copy: bool = False,
    ) -> Payload:
        """Registers an existing directory on disk as a payload for the bound agent
        template.

        Forwards to `PayloadsService.add_payload_directory`, injecting the agent
        template ID bound to this service so the caller does not need to supply it.

        Args:
            build_parameters: Parameters used to build the agent generator from the
                bound agent template (validated against the template).
            path: Path to the existing directory to register.
            payload_data: Arbitrary metadata attached to the payload. When `None`,
                no extra metadata is stored.
            payload_id: A previously reserved ID to assign to this payload. When
                `None`, a new ID is generated.
            name: A human-readable name for the payload directory. When `None`, the
                original directory name is used.
            description: An optional description for the payload.
            copy: When `False` (default) the source directory is moved into the
                repository. When `True` the source directory is copied and the original
                is left in place.

        Returns:
            The registered payload.

        Raises:
            AgentTemplateNotFoundError: If the bound agent template ID no longer exists.
            PayloadIDReservationNotFoundError: If `payload_id` is provided but has no
                corresponding reservation.
        """
        return self._payloads_service.add_payload_directory(
            agent_template_id=self._agent_template_id,
            build_parameters=build_parameters,
            path=path,
            payload_data=payload_data,
            payload_id=payload_id,
            name=name,
            description=description,
            copy=copy,
        )

    @log_and_propagate_error_on_service_method
    def delete_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> None:
        """Deletes a payload's repository resource and its associated metadata.

        Forwards to `PayloadsService.delete_payload_by_payload_id`. A
        `PAYLOAD_DELETED` event is only emitted when both the metadata and the
        repository resource existed prior to deletion. If only one side exists, a
        warning is logged and the orphaned side is cleaned up without emitting an
        event.

        Args:
            payload_id: The ID of the payload to delete.

        Returns:
            Nothing.

        Raises:
            PayloadNotFoundError: If neither payload metadata nor a matching repository
                resource exists.
        """
        self._payloads_service.delete_payload_by_payload_id(
            payload_id=payload_id,
        )

    @wraps(PayloadsService.get_payload_by_payload_id)
    @log_and_propagate_error_on_service_method
    def get_payload_by_payload_id(self, payload_id: str | uuid.UUID) -> Payload:
        """See `PayloadsService.get_payload_by_payload_id`."""
        return self._payloads_service.get_payload_by_payload_id(
            payload_id=payload_id,
        )

    @wraps(PayloadsService.get_all_payloads)
    @log_and_propagate_error_on_service_method
    def get_all_payloads(self) -> list[Payload]:
        """See `PayloadsService.get_all_payloads`."""
        return self._payloads_service.get_all_payloads()
