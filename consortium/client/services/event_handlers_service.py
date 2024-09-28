import asyncio
import json
from typing import Callable

import jsonschema
import websockets

from consortium.client.client_websockets_api_connection import (
    ClientWebsocketsAPIConnection,
)
from consortium.client.exceptions.client_websocket_api_connection_exceptions import (
    ClientWebsocketsAPIConnectionNotConnectedError,
    InvalidServerWebsocketAPIConnectionResponseError,
    SeverWebsocketAPIErrorResponseError,
)
from consortium.client.exceptions.event_handlers_service_exceptions import (
    EventHandlerAlreadyRegisteredError,
    EventHandlerNotRegisteredError,
    InvalidEventTypeError,
)

_websockets_api_generic_response_json_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["response", "event"]},
    },
}
_websockets_api_action_response_json_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["response"]},
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "data": {"type": "object"},
    },
}
_websockets_api_event_response_json_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["event"]},
        "event_type": {"type": "string"},
        "data": {"type": "object"},
    },
}


# Unlike the client REST API connections service, the event handlers service is unique
# per client session instance.
class EventHandlersService:
    def __init__(self, client_websockets_api_connection: ClientWebsocketsAPIConnection):
        self._client_websockets_api_connection = client_websockets_api_connection
        # The actual supported event types are queried from the websockets API at
        # runtime and then reassigned from the `init` class method that exists to allow
        # for asynchronous initialization to interact with the websocket.
        self._supported_event_types = []
        self._event_handlers = {}
        self._consume_websocket_message_tasks = set()
        self._websockets_api_response_messages = asyncio.Queue()

    def __str__(self) -> str:
        return "Event Handlers Service"

    def __repr__(self) -> str:
        return "EventHandlersService()"

    async def register_event_handler(
        self,
        event_type: str,
        event_handler: Callable[[dict], None],
    ):
        if not self._client_websockets_api_connection.connected:
            raise ClientWebsocketsAPIConnectionNotConnectedError
        if event_type not in self._supported_event_types:
            raise InvalidEventTypeError(event_type=str(event_type))
        if (
            event_type in self._event_handlers
            and event_handler in self._event_handlers[event_type]
        ):
            raise EventHandlerAlreadyRegisteredError(event_type=str(event_type))

        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

            await self._client_websockets_api_connection.send_message(
                action="register_event",
                events=[event_type],
            )
            # The response message is placed in a queue so that it can be consumed
            # by the main event loop while any event messages received before the
            # response message is sent from the server can be processed by the
            # event handlers.
            response = await self._websockets_api_response_messages.get()
            if not response["success"]:
                raise SeverWebsocketAPIErrorResponseError(
                    error_message=response["message"],
                )

        self._event_handlers[event_type].append(event_handler)

    # It is possible to register the same event handler function to multiple event
    # types. So when deregistering an event handler we specify the event type and the
    # event handler function to deregister.
    async def deregister_event_handler(
        self,
        event_type: str,
        event_handler: Callable[[dict], None],
    ):
        if not self._client_websockets_api_connection.connected:
            raise ClientWebsocketsAPIConnectionNotConnectedError
        if event_type not in self._supported_event_types:
            raise InvalidEventTypeError(event_type=str(event_type))
        if event_type not in self._event_handlers or (
            event_type in self._event_handlers
            and event_handler not in self._event_handlers[event_type]
        ):
            raise EventHandlerNotRegisteredError(event_type=str(event_type))

        found_event_handler = False
        for registered_event_handler in self._event_handlers[event_type]:
            if registered_event_handler == event_handler:
                self._event_handlers[event_type].remove(event_handler)
                found_event_handler = True
                break
        if not found_event_handler:
            assert False, (
                "Failed to deregister the provided event handler. The event handler "
                "was not found in the set of registered event handlers for the event "
                f"type '{event_type}'."
            )

        if not self._event_handlers[event_type]:
            del self._event_handlers[event_type]
            await self._client_websockets_api_connection.send_message(
                action="deregister_event",
                events=[event_type],
            )
            # The response message is placed in a queue so that it can be consumed
            # by the main event loop while any event messages received before the
            # response message is sent from the server can be processed by the
            # event handlers.
            response = await self._websockets_api_response_messages.get()
            if not response["success"]:
                raise SeverWebsocketAPIErrorResponseError(
                    error_message=response["message"],
                )

    @classmethod
    async def start_service(
        cls,
        client_websockets_api_connection: ClientWebsocketsAPIConnection,
    ):
        self = cls(client_websockets_api_connection)
        await self._client_websockets_api_connection.connect()

        try:
            await self._client_websockets_api_connection.send_message(
                action="get_all_events",
            )
            # No events are registered yet, so we can safely assume the first message
            # received is the response to the action request.
            response = await self._client_websockets_api_connection.recv_message()
            jsonschema.validate(response, _websockets_api_action_response_json_schema)
        except jsonschema.ValidationError:
            raise InvalidServerWebsocketAPIConnectionResponseError

        self._supported_event_types = response["data"]

        task = asyncio.create_task(self._consume_websocket_messages())
        self._consume_websocket_message_tasks.add(task)

        return self

    async def stop_service(self):
        for task in self._consume_websocket_message_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Reset whatever internal state was present from the previous websockets API
        # connection.
        self._supported_event_types = []
        self._event_handlers = {}
        self._consume_websocket_message_tasks = set()
        self._websockets_api_response_messages = asyncio.Queue()

    async def _consume_websocket_messages(self):
        try:
            while True:
                message = await self._client_websockets_api_connection.recv_message()
                jsonschema.validate(
                    message,
                    _websockets_api_generic_response_json_schema,
                )
                if message["type"] == "response":
                    jsonschema.validate(
                        message,
                        _websockets_api_event_response_json_schema,
                    )
                    await self._websockets_api_response_messages.put(message)
                # `message["type"]` can only take the value of `event` since we
                # performed the JSON schema validation on the general structure of a
                # response already.
                else:
                    jsonschema.validate(
                        message,
                        _websockets_api_event_response_json_schema,
                    )
                    event_type = message["event_type"]
                    data = message["data"]
                    if event_type in self._event_handlers:
                        for event_handler in self._event_handlers[event_type]:
                            await event_handler(data)
        except (websockets.exceptions.ConnectionClosedError, asyncio.CancelledError):
            pass
        except jsonschema.ValidationError:
            raise InvalidServerWebsocketAPIConnectionResponseError

        self._consume_websocket_message_tasks.remove(asyncio.current_task())
