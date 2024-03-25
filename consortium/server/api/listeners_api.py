from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.framework.framework_exceptions import (
    ListenerStartError,
    ListenerStopError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.listener_models import ListenerModel
from consortium.server.objects.listener_objects import ListenerState
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.server_exceptions import (
    InternalServerError,
    InvalidListenerOptionNameError,
    InvalidListenerOptionValueError,
    ListenerNotFoundError,
    ListenerStillRunningError,
    MethodNotAllowedError,
    UnauthorizedError,
)

router = APIRouter(
    prefix="/api/listeners",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
listeners_service = server_singletons.listeners_service


@router.get(
    "/all",
    responses={
        200: {"model": list[ListenerModel]},
    },
)
def get_all_listeners_info(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_LISTENERS_INFO)),
    ],
):
    return [
        ListenerModel(**listener.to_json())
        for listener in listeners_service.get_all_listeners()
    ]


@router.get(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {"model": ListenerNotFoundError().to_pydantic_model()},
    },
)
def get_listener_info_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_LISTENER_INFO_BY_LISTENER_ID),
        ),
    ],
):
    try:
        return ListenerModel(
            **listeners_service.get_listener_by_listener_id(listener_id).to_json(),
        )
    except KeyError:
        raise ListenerNotFoundError


@router.post(
    "/{listener_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStartError(message="string").to_pydantic_model()},
        404: {"model": ListenerNotFoundError().to_pydantic_model()},
    },
)
async def start_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.START_LISTENER_BY_LISTENER_ID)),
    ],
):
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
        # if start_listener fails, it will automatically raise ListenerStartError which
        # is caught by the exception handler at server_exception_handlers.py
        await listener.start_listener()
        return SuccessResponseModel()
    except KeyError:
        raise ListenerNotFoundError


@router.post(
    "/{listener_id}/stop",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStopError(message="string").to_pydantic_model()},
        404: {"model": ListenerNotFoundError().to_pydantic_model()},
    },
)
async def stop_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.STOP_LISTENER_BY_LISTENER_ID)),
    ],
):
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
        # if stop_listener fails, it will automatically raise ListenerStopError which is
        # caught by the exception handler at server_exception_handlers.py
        await listener.stop_listener()
        return SuccessResponseModel()
    except KeyError:
        raise ListenerNotFoundError(listener_id)


@router.put(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": ListenerNotFoundError().to_pydantic_model()},
        422: {
            "model": InvalidListenerOptionNameError(detail="string").to_pydantic_model()
            | InvalidListenerOptionValueError(detail="string").to_pydantic_model(),
        },
    },
)
def update_listener_by_listener_id(
    listener_id: str,
    new_listener_options: dict[str, Any],
    _: Annotated[None, Depends(AuthorizeUserRequest)],
):
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except KeyError:
        raise ListenerNotFoundError

    previous_listener_options = {
        option_name: option.get_option_value()
        for option_name, option in listener.options.items()
    }

    def revert_to_previous_listener_options():
        for (
            previous_option_name,
            previous_option_value,
        ) in previous_listener_options.items():
            listener.options[previous_option_name].set_option_value(
                previous_option_value,
            )

    for option_name, option_value in new_listener_options.items():
        try:
            listener.options[option_name].set_option_value(option_value)
        except KeyError:
            revert_to_previous_listener_options()
            raise InvalidListenerOptionNameError(
                detail=f'Listener option "{option_name}" does not exist',
            )
        except ValueError as exc:
            revert_to_previous_listener_options()
            raise InvalidListenerOptionValueError(detail=str(exc))
    return SuccessResponseModel()


@router.delete(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": ListenerNotFoundError().to_pydantic_model()},
        409: {"model": ListenerStillRunningError().to_pydantic_model()},
    },
)
def delete_listener_by_listener_id(
    listener_id: str,
    _: Annotated[None, Depends(AuthorizeUserRequest)],
):
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
        if listener.status.state == ListenerState.RUNNING:
            raise ListenerStillRunningError(
                detail="Stop the listener before attempting to delete it.",
            )
        listeners_service.remove_listener(listener)
        return SuccessResponseModel()
    except KeyError:
        raise ListenerNotFoundError(listener_id)
