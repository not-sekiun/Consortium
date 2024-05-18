from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.framework.base_listener_template import BaseListenerTemplate


# The listener profiles service is not defined at the module level like how it usually
# is because in this instance of the listener templates service it would create a
# circular import.
class ListenerTemplatesService:
    def __init__(self):
        self.listener_templates_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.listener_templates_service_logger.debug(
            f"Started {self}",
        )

    def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> BaseListenerTemplate:
        for listener_template in [
            listener_profile.listener_template
            for listener_profile in server_singletons.listener_profiles_service.get_all_listener_profiles()
        ]:
            if str(listener_template.listener_template_id) == listener_template_id:
                self.listener_templates_service_logger.debug(
                    f"Retrieved listener template: {listener_template!r}",
                )
                return listener_template
        raise ValueError(
            f"No listener template exists with the listener template ID: "
            f"{listener_template_id}",
        )

    def get_all_listener_templates(self) -> list[BaseListenerTemplate]:
        all_listener_templates = [
            listener_profile.listener_template
            for listener_profile in server_singletons.listener_profiles_service.get_all_listener_profiles()
        ]
        self.listener_templates_service_logger.debug(
            f"Retrieved all listener templates ({len(all_listener_templates)}"
            f"listener template(s) retrieved).",
        )
        return all_listener_templates

    def __str__(self) -> str:
        return "Consortium Listener Templates Service"

    def __repr__(self) -> str:
        return "ListenerTemplatesService()"
