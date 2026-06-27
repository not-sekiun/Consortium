import uuid

from loguru import logger

from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.server.exceptions.consortium_exceptions.listener_templates_consortium_exceptions import (
    ListenerTemplateIDNotFoundError,
    ListenerTemplateLabelNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class ListenerTemplatesService:
    def __init__(
        self,
        listener_profiles_service: ListenerProfilesService,
    ):
        self._listener_profiles_service = listener_profiles_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Listener Templates Service"

    def __repr__(self) -> str:
        return (
            f"ListenerTemplatesService("
            f"listener_profiles_service={self._listener_profiles_service!r}"
            f")"
        )

    @log_and_propagate_error_on_service_method
    def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str | uuid.UUID,
    ) -> BaseListenerTemplate:
        """Returns a listener template by its ID, searching across all loaded listener profiles.

        Args:
            listener_template_id (str | uuid.UUID): The ID of the listener template to
                retrieve.

        Returns:
            BaseListenerTemplate: The requested listener template.

        Raises:
            ListenerTemplateIDNotFoundError: If no listener template with the given ID
                is found.
        """
        listener_template_id = normalize_uuid(listener_template_id)

        for listener_template in [
            listener_profile.listener_template
            for listener_profile in self._listener_profiles_service.get_all_listener_profiles()
        ]:
            if str(listener_template.listener_template_id) == listener_template_id:
                self._logger.debug(
                    "Retrieved listener template by listener template ID '{}': {!r}",
                    listener_template_id,
                    listener_template,
                )
                return listener_template
        raise ListenerTemplateIDNotFoundError(
            listener_template_id=listener_template_id,
        )

    @log_and_propagate_error_on_service_method
    def get_listener_template_by_label(
        self,
        label: str,
    ) -> BaseListenerTemplate:
        """Returns a listener template by its label, searching across all loaded listener profiles.

        Args:
            label (str): The label of the listener template to retrieve.

        Returns:
            BaseListenerTemplate: The requested listener template.

        Raises:
            ListenerTemplateLabelNotFoundError: If no listener template with the given
                label is found.
        """
        for listener_template in [
            listener_profile.listener_template
            for listener_profile in self._listener_profiles_service.get_all_listener_profiles()
        ]:
            if listener_template.label == label:
                self._logger.debug(
                    "Retrieved listener template by label '{}': {!r}",
                    label,
                    listener_template,
                )
                return listener_template
        raise ListenerTemplateLabelNotFoundError(
            label=label,
        )

    @log_and_propagate_error_on_service_method
    def get_all_listener_templates(self) -> list[BaseListenerTemplate]:
        """Returns all listener templates across all loaded listener profiles.

        Returns:
            list[BaseListenerTemplate]: A list of all available listener templates.
                Empty if no listener profiles are loaded.
        """
        all_listener_templates = [
            listener_profile.listener_template
            for listener_profile in self._listener_profiles_service.get_all_listener_profiles()
        ]
        self._logger.debug(
            "Retrieved all listener templates ({} listener template(s) retrieved)",
            len(all_listener_templates),
        )
        return all_listener_templates
