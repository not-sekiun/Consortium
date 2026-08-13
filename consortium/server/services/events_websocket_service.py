from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

import jsonschema
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import JsonValue

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerNotRegisteredError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.events_service import EventsService

# The wire contract for every action message a client may send over the events
# websocket. Only the receive loop below validates against it, so it lives here rather
# than in the API layer.
_client_action_websocket_message_json_schema = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "subscribe",
                "unsubscribe",
                "get_subscribed_events",
                "get_unsubscribed_events",
                "get_all_events",
            ],
        },
        "events": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["action"],
    "allOf": [
        {
            "if": {"properties": {"action": {"enum": ["subscribe", "unsubscribe"]}}},
            "then": {"required": ["events"]},
        },
        {
            "if": {
                "properties": {
                    "action": {
                        "enum": [
                            "get_subscribed_events",
                            "get_unsubscribed_events",
                            "get_all_events",
                        ],
                    },
                },
            },
            "then": {"not": {"required": ["event"]}},
        },
    ],
}


class _ErrorResponseErrorCodes(StrEnum):
    INVALID_MESSAGE_FORMAT_ERROR = "INVALID_MESSAGE_FORMAT_ERROR"
    INVALID_EVENT_TYPE_ERROR = "INVALID_EVENT_TYPE_ERROR"
    ALREADY_SUBSCRIBED_TO_EVENT_ERROR = "ALREADY_SUBSCRIBED_TO_EVENT_ERROR"
    NOT_SUBSCRIBED_TO_EVENT_ERROR = "NOT_SUBSCRIBED_TO_EVENT_ERROR"


# One instance per accepted websocket connection. `_websocket_event_sender` is a bound
# method of this instance, which is what the events service keys its handler registry
# on, so every connection must get its own instance for the keys to stay distinct.
class _EventsWebsocketConnection:
    def __init__(self, websocket: WebSocket, events_service: EventsService):
        self._websocket = websocket
        self._events_service = events_service

    def _get_subscribed_events_for_websocket_event_sender(
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

    def _get_unsubscribed_events_for_websocket_event_sender(
        self,
        websocket_event_sender: Callable[[Event], Awaitable[None]],
    ) -> list[str]:
        all_events = self._events_service.get_all_event_types()
        subscribed_events = self._get_subscribed_events_for_websocket_event_sender(
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

    @staticmethod
    def _construct_errors_response_json(
        errors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "type": "response",
            "success": False,
            "errors": errors,
        }

    # Convenience wrapper for the (common) case of a single error: builds the one error
    # object and wraps it in the same `errors` list shape that every other error
    # response uses, so callers never need to know whether their failure is "a single
    # error" or "multiple errors", the response shape is always `{"errors": [...]}`.
    def _construct_single_error_response_json(
        self,
        code: _ErrorResponseErrorCodes,
        message: str,
        detail: dict[str, JsonValue] | None = None,
    ) -> dict[str, Any]:
        return self._construct_errors_response_json(
            errors=[
                self._construct_error_json(
                    code=code,
                    message=message,
                    detail=detail,
                ),
            ],
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
        subscribed_events = self._get_subscribed_events_for_websocket_event_sender(
            websocket_event_sender=self._websocket_event_sender,
        )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully retrieved subscribed events.",
                data=subscribed_events,
            ),
        )

    async def _handle_get_unsubscribed_events_action(self) -> None:
        unsubscribed_events = self._get_unsubscribed_events_for_websocket_event_sender(
            websocket_event_sender=self._websocket_event_sender,
        )
        await self._websocket.send_json(
            self._construct_success_response_json(
                message="Successfully retrieved unsubscribed events.",
                data=unsubscribed_events,
            ),
        )

    async def _handle_subscribe_action(self, action_message: dict[str, Any]) -> None:
        events_to_subscribe_to = action_message["events"]
        possible_events = list(EventType)
        subscribed_events = self._get_subscribed_events_for_websocket_event_sender(
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

    async def _handle_unsubscribe_action(self, action_message: dict[str, Any]) -> None:
        events_to_unsubscribe_from = action_message["events"]
        subscribed_events = self._get_subscribed_events_for_websocket_event_sender(
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

    async def run(self) -> None:
        try:
            while True:
                action_message = await self._websocket.receive_json()

                try:
                    jsonschema.validate(
                        action_message,
                        _client_action_websocket_message_json_schema,
                    )
                except jsonschema.ValidationError as exc:
                    await self._websocket.send_json(
                        self._construct_single_error_response_json(
                            code=_ErrorResponseErrorCodes.INVALID_MESSAGE_FORMAT_ERROR,
                            message=(
                                "Failed to process the client's action message. "
                                f"{exc.message}"
                            ),
                            detail=exc.cause,
                        ),
                    )
                    continue

                action = action_message["action"]

                if action == "get_all_events":
                    await self._handle_get_all_events_action()
                elif action == "get_subscribed_events":
                    await self._handle_get_subscribed_events_action()
                elif action == "get_unsubscribed_events":
                    await self._handle_get_unsubscribed_events_action()
                elif action == "subscribe":
                    await self._handle_subscribe_action(action_message=action_message)
                elif action == "unsubscribe":
                    await self._handle_unsubscribe_action(action_message=action_message)
                else:
                    # This should never happen because the JSON schema validation should
                    # catch this error at the top and send an error response back.
                    raise AssertionError(
                        "Invalid events websocket API message was received from "
                        "client. The client's action message was not recognized."
                    )
        except WebSocketDisconnect:
            for (
                event_type
            ) in self._events_service.get_event_types_from_registered_event_handler(
                event_handler=self._websocket_event_sender,
            ):
                self._events_service.deregister_event_handler_from_event_type(
                    event_type=event_type,
                    event_handler=self._websocket_event_sender,
                )


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

    async def run_connection(self, websocket: WebSocket) -> None:
        """Serves an already accepted events websocket connection until it disconnects.

        Runs the receive loop for the connection: validates each client action message
        against the events websocket message contract, dispatches it, and sends the
        response back over the same socket. Subscribing registers a per-connection
        event handler with the events service, which then pushes matching events to the
        client for as long as the connection lives. On client disconnect the connection
        is unsubscribed from every event type it subscribed to.

        The caller is responsible for authenticating, authorizing and accepting the
        websocket before calling this method.

        Args:
            websocket: An accepted websocket connection to serve.
        """
        connection = _EventsWebsocketConnection(
            websocket=websocket,
            events_service=self._events_service,
        )
        await connection.run()
