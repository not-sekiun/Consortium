from typing import Annotated, Callable, Coroutine

import jsonschema
from fastapi import APIRouter, Depends, WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.exceptions.service_exceptions.events_service_exceptions import (
    EventHandlerNotRegisteredError,
)
from consortium.server.objects.event_objects import EventType, Event
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

router = APIRouter(
    prefix="/api/events",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Events API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
events_service = server_singletons.events_service

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
        "event": {"type": "string", "enum": events_service.get_all_event_types()},
    },
    "required": ["action"],
    "allOf": [
        {
            "if": {"properties": {"action": {"enum": ["subscribe", "unsubscribe"]}}},
            "then": {"required": ["event"]},
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


def _get_subscribed_events_for_websocket_event_sender(
    websocket_event_sender: Callable[[Event], Coroutine[None, None, None]],
) -> list[str]:
    try:
        subscribed_events = (
            events_service.get_event_types_from_registered_event_handler(
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
    websocket_event_sender: Callable[[Event], Coroutine[None, None, None]],
) -> list[str]:
    all_events = events_service.get_all_event_types()
    subscribed_events = _get_subscribed_events_for_websocket_event_sender(
        websocket_event_sender=websocket_event_sender
    )
    return list(set(all_events) - set(subscribed_events))


def _websocket_event_sender(websocket: WebSocket):
    async def wrapper(event: Event):
        await websocket.send_json(
            {
                "type": "event",
                **event.to_json(),
            }
        )

    return wrapper


async def _handle_websocket(websocket: WebSocket):
    websocket_event_sender = _websocket_event_sender(websocket=websocket)

    while True:
        action_message = await websocket.receive_json()

        try:
            jsonschema.validate(
                action_message,
                _client_action_websocket_message_json_schema,
            )
        except jsonschema.ValidationError as exc:
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "error",
                    "message": f"Failed to process the client's action message. {exc.message}",
                    "data": exc.cause,
                },
            )

        action = action_message["action"]

        if action == "get_all_events":
            all_events = events_service.get_all_event_types()
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "success",
                    "message": "Successfully retrieved all events.",
                    "data": all_events,
                },
            )
        elif action == "get_subscribed_events":
            subscribed_events = _get_subscribed_events_for_websocket_event_sender(
                websocket_event_sender=websocket_event_sender,
            )
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "success",
                    "message": "Successfully retrieved subscribed events.",
                    "data": subscribed_events,
                },
            )
        elif action == "get_unsubscribed_events":
            unsubscribed_events = _get_unsubscribed_events_for_websocket_event_sender(
                websocket_event_sender=websocket_event_sender,
            )
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "success",
                    "message": "Successfully retrieved unsubscribed events.",
                    "data": unsubscribed_events,
                },
            )
        elif action == "subscribe":
            events_to_subscribe_to = action_message["events"]
            possible_events = list(EventType)
            subscribed_events = _get_subscribed_events_for_websocket_event_sender(
                websocket_event_sender=websocket_event_sender,
            )
            invalid_events = []
            for event in events_to_subscribe_to:
                if event not in possible_events:
                    invalid_events.append(
                        {
                            "event": event,
                            "reason": "The event type provided does not exist.",
                        },
                    )
                elif event in subscribed_events:
                    invalid_events.append(
                        {
                            "event": event,
                            "reason": (
                                "The event type provided has already been subscribed "
                                "to."
                            ),
                        },
                    )

            if invalid_events:
                await websocket.send_json(
                    {
                        "type": "response",
                        "status": "error",
                        "message": (
                            "Failed to subscribe to the provided events. All the "
                            "provided events must valid for a subscription request to "
                            "succeed. The following events are invalid: "
                            f"{", ".join([invalid_event["event"] for invalid_event in invalid_events])}."
                        ),
                        "data": invalid_events,
                    },
                )
                continue

            for event in events_to_subscribe_to:
                events_service.register_event_handler_to_event_type(
                    event_type=event,
                    event_handler=websocket_event_sender,
                )
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "success",
                    "message": "Successfully subscribed to the provided events.",
                    "data": None,
                },
            )
        elif action == "unsubscribe":
            events_to_unsubscribe_from = action_message["events"]
            invalid_events = []
            subscribed_events = _get_subscribed_events_for_websocket_event_sender(
                websocket_event_sender=websocket_event_sender,
            )
            possible_events = list(EventType)

            for event in events_to_unsubscribe_from:
                if event not in possible_events:
                    invalid_events.append(
                        {
                            "event": event,
                            "reason": "The event type provided does not exist.",
                        },
                    )
                elif event not in subscribed_events:
                    invalid_events.append(
                        {
                            "event": event,
                            "reason": (
                                "The event type provided has not been subscribed to."
                            ),
                        },
                    )

            if invalid_events:
                await websocket.send_json(
                    {
                        "type": "response",
                        "status": "error",
                        "message": (
                            "Failed to unsubscribe to the provided events. All the "
                            "provided events must valid for an unsubscription request "
                            "to succeed. The following events are invalid: "
                            f"{", ".join([invalid_event["event"] for invalid_event in invalid_events])}."
                        ),
                        "data": invalid_events,
                    },
                )
                continue

            for event in events_to_unsubscribe_from:
                events_service.deregister_event_handler_from_event_type(
                    event_type=event,
                    event_handler=websocket_event_sender,
                )
            await websocket.send_json(
                {
                    "type": "response",
                    "status": "success",
                    "message": "Successfully unsubscribed from the provided events.",
                    "data": None,
                },
            )
        else:
            assert False, (
                "Invalid events websocket API message was received from client. "
                "The client's action message was not recognized."
            )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    # TODO: Abstract the process of authorizing users, creating roles, and editing role
    #  permissions. For now we use this hack to check permissions specifically for this
    #  websocket endpoint.
    if (
        UserPermissions.USE_EVENTS_WEBSOCKET
        not in AuthorizeUserRequest.ROLE_PERMISSIONS[user.role]
    ):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    await websocket.accept()
    await _handle_websocket(websocket)
