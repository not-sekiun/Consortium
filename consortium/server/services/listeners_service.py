import copy
from typing import Any

from loguru import logger

from consortium.framework.base_listener import BaseListener
from consortium.server.exceptions.framework_exceptions.listeners_framework_exceptions import (
    ListenerAlreadyRunningError as ListenerAlreadyRunningFrameworkError,
    ListenerNotRunningError as ListenerNotRunningFrameworkError,
    ListenerStartError as ListenerStartFrameworkError,
    ListenerStopError as ListenerStopFrameworkError,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.service_exceptions.listeners_service_exceptions import (
    InvalidListenerParameterNameError,
    InvalidListenerParameterValueError,
    ListenerAlreadyExistsError,
    ListenerAlreadyRunningError as ListenerAlreadyRunningServiceError,
    ListenerNotFoundError,
    ListenerNotRunningError as ListenerNotRunningServiceError,
    ListenerStartError as ListenerStartServiceError,
    ListenerStopError as ListenerStopServiceError,
)
from consortium.server.objects.listener_objects import ListenerState
from consortium.server.services.listener_templates_service import (
    ListenerTemplatesService,
)


class ListenersService:
    def __init__(self, listener_templates_service: ListenerTemplatesService):
        self._listener_templates_service = listener_templates_service
        self._listeners = {}
        self.listeners_service_logger = logger.bind(logger_name=str(self))
        self.listeners_service_logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Consortium Listeners Service"

    def __repr__(self) -> str:
        return (
            f"ListenersService("
            f"listener_templates_service={self._listener_templates_service!r}"
            f")"
        )

    def get_listener_by_listener_id(self, listener_id: str) -> BaseListener:
        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise ListenerNotFoundError(listener_id=listener_id)

        self.listeners_service_logger.debug(f"Retrieved listener: {listener!r}")
        return listener

    def get_all_listeners(self) -> list[BaseListener]:
        all_listeners = list(self._listeners.values())
        self.listeners_service_logger.debug(
            f"Retrieved all listeners ({len(all_listeners)} retrieved)",
        )
        return all_listeners

    def create_listener_from_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
        options: dict[str, Any],
    ) -> BaseListener:
        listener_template = self._listener_templates_service.get_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
        )
        for option_name, option_value in options.items():
            listener_template.set_option_value_by_option_name(
                option_name=option_name,
                option_value=option_value,
            )
        listener = listener_template.create_listener()
        self._listeners[str(listener.listener_id)] = listener
        self.listeners_service_logger.info(f"Created listener: {listener}")
        self.listeners_service_logger.debug(f"Created listener: {listener!r}")
        return listener

    def add_listener(self, listener: BaseListener) -> None:
        if str(listener.listener_id) in self._listeners:
            raise ListenerAlreadyExistsError
        self._listeners[str(listener.listener_id)] = listener

    def remove_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        if listener.status.state == ListenerState.RUNNING:
            raise ListenerAlreadyRunningServiceError

        removed_listener = self._listeners.pop(listener_id)
        self.listeners_service_logger.info(f"Removed listener: {removed_listener}")
        self.listeners_service_logger.debug(f"Removed listener: {removed_listener!r}")

    def update_listener_name_by_listener_id(
        self,
        listener_id: str,
        name: str,
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        old_name = listener.name
        listener.name = name
        self.listeners_service_logger.info(
            f"Updated name for listener {listener}: '{old_name}' -> '{name}'",
        )
        return listener

    def update_listener_description_by_listener_id(
        self,
        listener_id: str,
        description: str,
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        old_description = listener.description
        listener.description = description
        self.listeners_service_logger.info(
            f"Updated description for listener {listener}: '{old_description}' -> "
            f"'{description}'",
        )
        return listener

    def update_listener_parameters_by_listener_id(
        self,
        listener_id: str,
        new_parameters: dict[str, Any],
    ) -> BaseListener:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)

        if listener.status.state == ListenerState.RUNNING:
            raise ListenerAlreadyRunningServiceError

        # It should be impossible for this for loop to break out without finding
        # the listener template that matches the target listener or to trip up on a
        # false positive based on listener type because all listener types are
        # unique to their respective listener.
        found_listener_template = False
        for (
            test_listener_template
        ) in self._listener_templates_service.get_all_listener_templates():
            if test_listener_template.listener_type == listener.listener_type:
                found_listener_template = True
                listener_template = test_listener_template
                break
        # This should never be raised unless a programmer error is made.
        assert (
            found_listener_template
        ), "Listener template resolution failed unexpectedly"

        for parameter_name, parameter_value in listener.parameters.items():
            if parameter_name not in new_parameters:
                # parameter_value could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                new_parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in new_parameters.items():
            if parameter_name not in listener_template.options:
                raise InvalidListenerParameterNameError(
                    parameter_name=parameter_name,
                    listener=str(listener),
                )
            new_parameters[parameter_name] = parameter_value

        # At this point new_parameters contains all the parameters that a listener
        # would have. Any parameters not specified in the request body as part of
        # the JSON under the key "parameters" will be the same as the previous
        # listener.
        for parameter_name, parameter_value in new_parameters.items():
            try:
                listener_template.options[
                    parameter_name
                ].set_option_value_by_option_name(
                    parameter_value,
                )
            except OptionValueValidationError as exc:
                raise InvalidListenerParameterValueError(
                    parameter_name=parameter_name,
                    parameter_value=str(parameter_value),
                    listener=str(listener),
                    validation_error_message=str(exc),
                )

        # Create a temporary listener whose attributes we copy over to the
        # existing listener. This allows us to perform the name and
        # endpoint resolution required to update the attribute without
        # inadvertently overwriting any existing state within the existing
        # listener.
        temporary_listener = listener_template.create_listener()
        listener.name = temporary_listener.name
        listener.endpoint = temporary_listener.endpoint
        listener.parameters = copy.deepcopy(temporary_listener.parameters)

        self.listeners_service_logger.info(
            f"Updated parameters for listeners {listener}: {new_parameters}",
        )
        return listener

    async def start_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        try:
            await listener.start_listener()
        except ListenerStartFrameworkError as exc:
            raise ListenerStartServiceError(
                message=str(exc),
                detail=exc.detail,
            ) from None
        except ListenerAlreadyRunningFrameworkError as exc:
            raise ListenerNotRunningServiceError(message=exc.message) from None

    async def stop_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        try:
            await listener.stop_listener()
        except ListenerStopFrameworkError as exc:
            raise ListenerStopServiceError(
                message=str(exc),
                detail=exc.detail,
            ) from None
        except ListenerNotRunningFrameworkError as exc:
            raise ListenerNotRunningServiceError(message=exc.message) from None

    async def cancel_listener_by_listener_id(self, listener_id: str) -> None:
        listener = self.get_listener_by_listener_id(listener_id=listener_id)
        try:
            await listener.cancel_listener()
        except ListenerNotRunningFrameworkError as exc:
            raise ListenerNotRunningServiceError(message=exc.message) from None
