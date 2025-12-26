import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import jsonschema
import websockets
from loguru import logger

from consortium.client.exceptions.websockets_api_exceptions import (
    EventHandlerNotSubscribedError,
    EventTypeNotSubscribedError,
    InvalidEventTypeError,
    InvalidServerWebsocketAPIResponseError,
    SeverWebsocketsApiErrorResponseError,
    WebsocketsApiAlreadyConnectedError,
    WebsocketsApiHandlerAlreadyRunningError,
    WebsocketsApiHandlerNotRunningError,
    WebsocketsAPINotConnectedError,
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


class WebsocketsApi:
    def __init__(self, remote_host: str, remote_port: int):
        self.remote_host = remote_host
        self.remote_port = remote_port

        self.json_web_token = None
        self.connected = False
        self.running = False

        self._websocket = None
        self._websocket_message_handler_task = None
        self._logger = logger.bind(
            logger_name=str(self),
        )
        self._event_handlers = {}
        self._websocket_action_response_messages_queue = asyncio.Queue()

    async def connect(self, json_web_token: str) -> None:
        if self.connected:
            raise WebsocketsApiAlreadyConnectedError

        self._websocket = await websockets.connect(
            f"ws://{self.remote_host}:{self.remote_port}/api/events",
            additional_headers={"Authorization": f"Bearer {json_web_token}"},
        )

        self.json_web_token = json_web_token
        self.connected = True

    async def disconnect(self) -> None:
        if not self.connected:
            raise WebsocketsAPINotConnectedError

        await self._websocket.close()

        self.connected = False
        self.json_web_token = None

    async def start(self) -> None:
        if self.running:
            raise WebsocketsApiHandlerAlreadyRunningError

        self._websocket_message_handler_task = asyncio.create_task(
            self._websocket_message_handler_loop(),
        )

        self.running = True

    async def stop(self) -> None:
        if not self.running:
            raise WebsocketsApiHandlerNotRunningError

        self._websocket_message_handler_task.cancel()
        # There is a non-negligible amount of time that passes between the time the
        # task is cancelled and the time the task actually stops running. So we await
        # the task to ensure that the task has actually stopped running before we
        # continue.
        await self._websocket_message_handler_task

        self.running = False

    async def subscribe_to_event(
        self,
        event_type: str,
        event_handler: Callable[[dict[str, Any]], Awaitable[None]],
    ):
        if event_type not in self._event_handlers:
            # If the event type is not valid, the server will return an error response.
            # The error response when received will raise a
            # ServerWebsocketsAPIErrorResponseError exception that will prevent the
            # rest of the method from executing.
            await self._send_and_recv_message(action="subscribe", events=[event_type])
            self._event_handlers[event_type] = [event_handler]
        else:
            self._event_handlers[event_type].append(event_handler)

    async def unsubscribe_from_event(
        self,
        event_type: str,
        event_handler: Callable[[dict[str, Any]], Awaitable[None]] | None,
    ):
        if event_type not in self._event_handlers:
            raise EventTypeNotSubscribedError(event_type=event_type)
        # If no event handler is provided, all event handlers for the event type are
        # removed and we unsubscribe from the event over the server's websockets API
        # because we no longer have any event handlers for the event type.
        if event_handler is None or len(self._event_handlers[event_type]) == 1:
            await self._send_and_recv_message(action="unsubscribe", events=[event_type])
            del self._event_handlers[event_type]
            return
        if event_handler not in self._event_handlers[event_type]:
            raise EventHandlerNotSubscribedError(event_type=event_type)

        self._event_handlers[event_type].remove(event_handler)

    async def get_all_events(self):
        return (await self._send_and_recv_message(action="get_all_events"))["data"]

    async def get_subscribed_events(self):
        return (await self._send_and_recv_message(action="get_subscribed_events"))[
            "data"
        ]

    async def get_unsubscribed_events(self):
        return (await self._send_and_recv_message(action="get_unsubscribed_events"))[
            "data"
        ]

    async def get_all_event_handlers(
        self,
    ) -> dict[str, list[Callable[[dict[str, Any]], None]]]:
        return self._event_handlers

    async def get_event_handlers_by_event_type(
        self,
        event_type: str,
    ) -> list[Callable[[dict[str, Any]], None]]:
        if event_type not in self._event_handlers:
            raise InvalidEventTypeError(event_type=event_type)
        return self._event_handlers.get(event_type, [])

    async def _send_message(
        self,
        action: str,
        events: list[str] = None,
    ) -> None:
        if not self.connected:
            raise WebsocketsAPINotConnectedError

        if events is None:
            message = {"action": action}
        else:
            message = {"action": action, "events": events}

        await self._websocket.send(json.dumps(message))

        self._logger.debug("Sent message: {}", message)

    async def _recv_message(self) -> dict[str, Any]:
        if not self.connected:
            raise WebsocketsAPINotConnectedError

        if not self.running:
            message = await self._websocket.recv()
        else:
            # If the websocket message handler loop is running, we need to get the
            # response message from the queue rather than from the websocket directly.
            message = await self._websocket_action_response_messages_queue.get()

        try:
            message_json = json.loads(message)
        except json.JSONDecodeError:
            raise InvalidServerWebsocketAPIResponseError from None

        self._logger.debug(
            "Received message: {}",
            message_json,
        )

        if not message_json["success"]:
            raise SeverWebsocketsApiErrorResponseError(
                error_message=(
                    f"{message_json['error']['code']}: "
                    f"{message_json['error']['message']}"
                ),
            )

        return message

    async def _send_and_recv_message(
        self,
        action: str,
        events: list[str] = None,
    ) -> dict[str, Any]:
        await self._send_message(action=action, events=events)
        return await self._recv_message()

    async def _websocket_message_handler_loop(self) -> None:
        try:
            while True:
                raw_message = await self._websocket.recv()

                try:
                    message = json.loads(raw_message)
                    jsonschema.validate(
                        message,
                        _websockets_api_generic_response_json_schema,
                    )
                except (json.JSONDecodeError, jsonschema.ValidationError):
                    raise InvalidServerWebsocketAPIResponseError from None

                # If the message is a response message, we place it in a queue so that
                # it can be consumed by any calls to the `_recv_message` method in the
                # main event loop while any event messages received before the response
                # message is sent from the server can be processed by the event
                # handlers.
                if message["type"] == "response":
                    await self._websocket_action_response_messages_queue.put(
                        raw_message,
                    )
                elif message["type"] == "event":
                    event_type = message["event_type"]
                    if event_type in self._event_handlers:
                        for event_handler in self._event_handlers[event_type]:
                            try:
                                await event_handler(message)
                            except Exception as exc:
                                # This should never happen unless there is a bug in the
                                # event handler itself that the developer did not catch.
                                self._logger.error(
                                    "Failed to process the received websocket message. "
                                    "The event handler for the event of event type "
                                    f"'{event_type}' raised an exception: {exc}. If "
                                    f"you are seeing this message, something very "
                                    "wrong has happened. Please report it to the "
                                    "developer at github.com/not-sekiun.",
                                )
                else:
                    # This should never happen unless there is a mismatch between the
                    # source code of the events API on the server side and the
                    # websockets api connection abstraction object on the client side.
                    self._logger.error(
                        "Failed to process the received websocket message. The message "
                        f"type '{message['type']}' is not supported. If you are seeing "
                        "this message, something very wrong has happened. Please "
                        "report it to the developer at github.com/not-sekiun.",
                    )
        except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
            asyncio.CancelledError,
        ):
            pass
