from loguru import logger

from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions import (
    ListenerTemplateNotFoundError,
)
from consortium.server.server_logging import LoggerType
from consortium.server.services.listener_profiles_service import ListenerProfilesService


# The listener profiles service is not defined at the module level like how it is
# usually because it would create a circular import here.
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
        return "ListenerTemplatesService()"

    def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> BaseListenerTemplate:
        for listener_template in [
            listener_profile.listener_template
            for listener_profile in self._listener_profiles_service.get_all_listener_profiles()
        ]:
            if str(listener_template.listener_template_id) == listener_template_id:
                self._logger.debug(
                    "Retrieved listener template: {!r}",
                    listener_template,
                )
                return listener_template
        raise ListenerTemplateNotFoundError(
            listener_template_id=listener_template_id,
        )

    def get_all_listener_templates(self) -> list[BaseListenerTemplate]:
        all_listener_templates = [
            listener_profile.listener_template
            for listener_profile in self._listener_profiles_service.get_all_listener_profiles()
        ]
        self._logger.debug(
            "Retrieved all listener templates ({} listener template(s) retrieved).",
            len(all_listener_templates),
        )
        return all_listener_templates
