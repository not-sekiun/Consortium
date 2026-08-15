import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    ValidationError,
)
from pydantic_core import ErrorDetails

from consortium.framework._core.utils import _format_validation_error_location
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerNotRegisteredError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_objects import User
from consortium.server.services.events_service import EventsService
from consortium.server.utils import log_and_propagate_error_on_service_method


# The wire contract for every action message a client may send over the events
# websocket. Only the receive loop below validates against it, so it lives here rather
# than in the API layer. Unknown fields are rejected rather than ignored, which is what
# holds the "omit `events` entirely for the actions that do not take it" half of the
# contract: an action carrying fields it has no use for is a client that has misread the
# contract, and is worth saying so about.
class _BaseClientActionMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Event strings stay unvalidated here: an unknown event type is answered per event with
# its own error code by the subscribe and unsubscribe handlers, rather than failing the
# whole message as a format error.
class _SubscribeActionMessage(_BaseClientActionMessage):
    action: Literal["subscribe"]
    events: list[str]


class _UnsubscribeActionMessage(_BaseClientActionMessage):
    action: Literal["unsubscribe"]
    events: list[str]


class _GetSubscribedEventsActionMessage(_BaseClientActionMessage):
    action: Literal["get_subscribed_events"]


class _GetUnsubscribedEventsActionMessage(_BaseClientActionMessage):
    action: Literal["get_unsubscribed_events"]


class _GetAllEventsActionMessage(_BaseClientActionMessage):
    action: Literal["get_all_events"]


_ClientActionMessage = Annotated[
    _SubscribeActionMessage
    | _UnsubscribeActionMessage
    | _GetSubscribedEventsActionMessage
    | _GetUnsubscribedEventsActionMessage
    | _GetAllEventsActionMessage,
    Field(discriminator="action"),
]

_client_action_message_adapter: TypeAdapter[_ClientActionMessage] = TypeAdapter(
    _ClientActionMessage,
)


class _ErrorResponseErrorCodes(StrEnum):
    INVALID_MESSAGE_FORMAT_ERROR = "INVALID_MESSAGE_FORMAT_ERROR"
    INVALID_EVENT_TYPE_ERROR = "INVALID_EVENT_TYPE_ERROR"
    ALREADY_SUBSCRIBED_TO_EVENT_ERROR = "ALREADY_SUBSCRIBED_TO_EVENT_ERROR"
    NOT_SUBSCRIBED_TO_EVENT_ERROR = "NOT_SUBSCRIBED_TO_EVENT_ERROR"


# One instance per accepted websocket connection. `_websocket_event_sender` is a bound
# method of this instance, which is what the events service keys its handler registry
# on, so every connection must get its own instance for the keys to stay distinct.
class _EventsWebsocketHandler:
    def __init__(self, websocket: WebSocket, events_service: EventsService):
        self._websocket = websocket
        self._events_service = events_service

    def _get_subscribed_events(
        self,
        websocket_event_sender: Callable[[Event], Awaitable[None]],
    ) -> list[str]:
        try:
            subscribed_events = (
                self._events_service.get_event_types_from_registered_event_handler(
                    event_handler=websocket_event_sender,
                )
            )
        # When this error is raised it means that particular websocket did not
        # subscribe to any events. Hence, its send function is not registered which
        # causes the error.
        except EventHandlerNotRegisteredError:
            subscribed_events = []
        return subscribed_events

    def _get_unsubscribed_events(
        self,
        websocket_event_sender: Callable[[Event], Awaitable[None]],
    ) -> list[str]:
        all_events = self._events_service.get_all_event_types()
        subscribed_events = self._get_subscribed_events(
            websocket_event_sender=websocket_event_sender,
        )
        return list(set(all_events) - set(subscribed_events))

    async def _websocket_event_sender(self, event: Event) -> None:
        await self._websocket.send_json(
            {
                "type": "event",
                **event.to_json(),
            },
        )

    @staticmethod
    def _construct_success_response_json(
        message: str,
        data: Any | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "response",
            "success": True,
            "message": message,
            "data": data,
        }

    @staticmethod
    def _construct_errors_response_json(
        errors: list[dict[str, JsonValue]],
    ) -> dict[str, JsonValue]:
        return {
            "type": "response",
            "success": False,
            "errors": errors,
        }

    @staticmethod
    def _construct_error_json(
        code: _ErrorResponseErrorCodes,
        message: str,
        detail: dict[str, JsonValue] | None = None,
    ) -> dict[str, Any]:
        return {
            "code": code,
            "message": message,
            "detail": detail,
        }

    def _construct_single_error_response_json(
        self,
        code: _ErrorResponseErrorCodes,
        message: str,
        detail: dict[str, JsonValue] | None = None,
    ) -> dict[str, JsonValue]:
        return self._construct_errors_response_json(
            errors=[
                self._construct_error_json(
                    code=code,
                    message=message,
                    detail=detail,
                ),
            ],
        )

    # Pydantic prefixes the path of every error it finds inside a tagged union with the
    # tag it matched, so a missing `events` is reported at `("subscribe", "events")`.
    # That first entry names the model, not a field of the flat message the client sent,
    # so it is dropped to leave a path the client can locate in what it sent. An error
    # against the message as a whole, such as an unrecognized action, has no path left to
    # report and so is stated on its own.
    @staticmethod
    def _format_validation_error_cause(error: ErrorDetails) -> str:
        location = _format_validation_error_location(location=error["loc"][1:])
        if not location:
            return f"{error['msg']}."
        return f"`{location}`: {error['msg']}."

    # A message that fails validation fails as a whole, nothing about it was acted on, so
    # it is answered with one error rather than one per violation the way a batch
    # subscribe reports a result per event. Every violation still reaches the client:
    # each is named in the message qualified by the field it sits on, and the pydantic
    # errors are carried raw in the detail for clients that would rather read the paths
    # than the sentence. The `url` pydantic attaches to each error is dropped because it
    # points at pydantic's own docs and pins the version this server happens to run.
    def _construct_message_format_errors_response_json(
        self,
        validation_error: ValidationError,
    ) -> dict[str, JsonValue]:
        errors = validation_error.errors()
        causes = " ".join(
            self._format_validation_error_cause(error=error) for error in errors
        )
        return self._construct_single_error_response_json(
            code=_ErrorResponseErrorCodes.INVALID_MESSAGE_FORMAT_ERROR,
            message=f"Failed to process the client's action message. {causes}",
            detail={"validation_errors": errors},
        )

    async def _handle_get_all_events_action(self) -> None:
        all_events = self._events_service.get_all_event_types()
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully retrieved all events.",
                data=all_events,
            ),
        )

    async def _handle_get_subscribed_events_action(self) -> None:
        subscribed_events = self._get_subscribed_events(
            websocket_event_sender=self._websocket_event_sender,
        )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully retrieved subscribed events.",
                data=subscribed_events,
            ),
        )

    async def _handle_get_unsubscribed_events_action(self) -> None:
        unsubscribed_events = self._get_unsubscribed_events(
            websocket_event_sender=self._websocket_event_sender,
        )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully retrieved unsubscribed events.",
                data=unsubscribed_events,
            ),
        )

    async def _handle_subscribe_action(
        self,
        action_message: _SubscribeActionMessage,
    ) -> None:
        events_to_subscribe_to = action_message.events
        possible_events = list(EventType)
        subscribed_events = self._get_subscribed_events(
            websocket_event_sender=self._websocket_event_sender,
        )
        errors = []
        for event in events_to_subscribe_to:
            if event not in possible_events:
                errors.append(
                    self._construct_error_json(
                        code=_ErrorResponseErrorCodes.INVALID_EVENT_TYPE_ERROR,
                        message=(
                            "Failed to subscribe to event. The provided event "
                            f"type '{event}' does not exist."
                        ),
                        detail={"event": event},
                    ),
                )
            elif event in subscribed_events:
                errors.append(
                    self._construct_error_json(
                        code=_ErrorResponseErrorCodes.ALREADY_SUBSCRIBED_TO_EVENT_ERROR,
                        message=(
                            "Failed to subscribe to event. The provided event "
                            f"type '{event}' has already been subscribed to."
                        ),
                        detail={"event": event},
                    ),
                )

        if errors:
            await self._websocket.send_json(
                self._construct_errors_response_json(
                    errors=errors,
                ),
            )
            return

        for event in events_to_subscribe_to:
            self._events_service.register_event_handler_to_event_type(
                event_type=event,
                event_handler=self._websocket_event_sender,
            )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully subscribed to the provided events.",
            ),
        )

    async def _handle_unsubscribe_action(
        self,
        action_message: _UnsubscribeActionMessage,
    ) -> None:
        events_to_unsubscribe_from = action_message.events
        subscribed_events = self._get_subscribed_events(
            websocket_event_sender=self._websocket_event_sender,
        )
        possible_events = list(EventType)
        errors = []
        for event in events_to_unsubscribe_from:
            if event not in possible_events:
                errors.append(
                    self._construct_error_json(
                        code=_ErrorResponseErrorCodes.INVALID_EVENT_TYPE_ERROR,
                        message=(
                            "Failed to unsubscribe from event. The provided event "
                            f"type '{event}' does not exist."
                        ),
                    ),
                )
            elif event not in subscribed_events:
                errors.append(
                    self._construct_error_json(
                        code=_ErrorResponseErrorCodes.NOT_SUBSCRIBED_TO_EVENT_ERROR,
                        message=(
                            "Failed to unsubscribe from event. The provided event "
                            f"type '{event}' has not been subscribed to."
                        ),
                    ),
                )

        if errors:
            await self._websocket.send_json(
                self._construct_errors_response_json(
                    errors=errors,
                ),
            )
            return

        for event in events_to_unsubscribe_from:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event,
                event_handler=self._websocket_event_sender,
            )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully unsubscribed from the provided events.",
            ),
        )

    # Removes every subscription this connection holds. Called from `run`'s `finally`
    # rather than from its disconnect handler so that cleanup does not depend on how the
    # receive loop ended: an exception out of the loop, or cancellation at shutdown, would
    # otherwise leave this connection's sender registered with the events service against a
    # socket that is already gone, where every later trigger of that event type would call
    # it and fail.
    def _deregister_all_subscriptions(self) -> None:
        subscribed_event_types = (
            self._events_service.get_event_types_from_registered_event_handler(
                event_handler=self._websocket_event_sender,
            )
        )
        for event_type in subscribed_event_types:
            self._events_service.deregister_event_handler_from_event_type(
                event_type=event_type,
                event_handler=self._websocket_event_sender,
            )

    async def run(self) -> None:
        try:
            while True:
                try:
                    raw_action_message = await self._websocket.receive_json()
                # `receive_json` decodes the frame before this loop ever sees it, so a
                # frame that is not decodable fails here rather than at the model
                # validation below: text that is not valid JSON raises `JSONDecodeError`,
                # and a binary frame raises `KeyError` because starlette reads the `text`
                # key off a message that carries `bytes` instead.
                except json.JSONDecodeError, KeyError:
                    await self._websocket.send_json(
                        self._construct_single_error_response_json(
                            code=_ErrorResponseErrorCodes.INVALID_MESSAGE_FORMAT_ERROR,
                            message=(
                                "Failed to process the client's action message. The "
                                "message must be a text frame containing valid JSON."
                            ),
                        ),
                    )
                    continue

                try:
                    action_message = _client_action_message_adapter.validate_python(
                        raw_action_message,
                    )
                except ValidationError as exc:
                    await self._websocket.send_json(
                        self._construct_message_format_errors_response_json(
                            validation_error=exc,
                        ),
                    )
                    continue

                match action_message:
                    case _GetAllEventsActionMessage():
                        await self._handle_get_all_events_action()
                    case _GetSubscribedEventsActionMessage():
                        await self._handle_get_subscribed_events_action()
                    case _GetUnsubscribedEventsActionMessage():
                        await self._handle_get_unsubscribed_events_action()
                    case _SubscribeActionMessage():
                        await self._handle_subscribe_action(
                            action_message=action_message,
                        )
                    case _UnsubscribeActionMessage():
                        await self._handle_unsubscribe_action(
                            action_message=action_message,
                        )
                    case _:
                        # This should never happen because validation above only ever
                        # produces one of the models matched on here.
                        raise AssertionError(
                            "Invalid events websocket API message was received from "
                            "client. The client's action message was not recognized."
                        )
        # A client going away is how a connection normally ends, so it is swallowed here
        # and never reported as an error. Every other way out of the loop propagates.
        except WebSocketDisconnect:
            pass
        finally:
            self._deregister_all_subscriptions()


class EventsWebsocketService:
    def __init__(self, events_service: EventsService):
        self._events_service = events_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self):
        return "Events Websocket Service"

    def __repr__(self):
        return "EventsWebsocketService()"

    @log_and_propagate_error_on_service_method
    async def handle_connection(self, websocket: WebSocket, user: User) -> None:
        """Serves an already accepted events websocket connection until it disconnects.

        Runs the receive loop for the connection: validates each client action message
        against the events websocket message contract, dispatches it, and sends the
        response back over the same socket. A message that is malformed, whether it is
        undecodable or fails the contract, is answered with an error response and leaves
        the connection open. Subscribing registers a per-connection event handler with
        the events service, which then pushes matching events to the client for as long
        as the connection lives. However the connection ends, it is unsubscribed from
        every event type it subscribed to.

        The caller is responsible for authenticating, authorizing and accepting the
        websocket before calling this method.

        Args:
            websocket: An accepted websocket connection to serve.
            user: The authenticated user the connection belongs to.
        """
        self._logger.info("{} made a WebSocket connection to the events API.", user)

        handler = _EventsWebsocketHandler(
            websocket=websocket,
            events_service=self._events_service,
        )
        await handler.run()
