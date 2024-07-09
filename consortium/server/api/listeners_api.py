from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.listeners_api_exceptions import (
    InvalidListenerParameterNameError,
    InvalidListenerParameterValueError,
    ListenerAlreadyRunningError as ListenerAlreadyRunningAPIError,
    ListenerCancellationError,
    ListenerNotFoundError as ListenerNotFoundAPIError,
    ListenerNotRunningError,
    ListenerStartError as ListenerStartAPIError,
    ListenerStopError as ListenerStopAPIError,
    ListenerTemplateResolutionError,
)
from consortium.server.exceptions.service_exceptions.listeners_service_exceptions import (
    InvalidListenerParameterNameError as InvalidListenerParameterNameServiceError,
    InvalidListenerParameterValueError as InvalidListenerParameterValueServiceError,
    ListenerAlreadyRunningError as ListenerAlreadyRunningServiceError,
    ListenerNotFoundError as ListenerNotFoundServiceError,
    ListenerStartError as ListenerStartServiceError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.listener_models import ListenerModel
from consortium.server.objects.example_objects import example_listener_type
from consortium.server.objects.listener_objects import ListenerState
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/listeners",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Listeners API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
listeners_service = server_singletons.listeners_service
listener_templates_service = server_singletons.listener_templates_service


@router.get(
    "/all",
    responses={
        200: {"model": list[ListenerModel]},
    },
)
def get_all_listeners(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_LISTENERS)),
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
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def get_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_LISTENER_BY_LISTENER_ID),
        ),
    ],
):
    try:
        return ListenerModel(
            **listeners_service.get_listener_by_listener_id(listener_id).to_json(),
        )
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)


@router.post(
    "/{listener_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStartAPIError().to_pydantic_model()},
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        409: {"model": ListenerAlreadyRunningAPIError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def start_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.START_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)

    if listener.status.state == ListenerState.RUNNING:
        raise ListenerAlreadyRunningAPIError(
            message="The listener cannot be started because it is already running",
        )

    try:
        await listener.start_listener()
    except FrameworkListenerStartError as exc:
        raise ListenerStartError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerErrorError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.post(
    "/{listener_id}/stop",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStopAPIError(message="string").to_pydantic_model()},
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        409: {"model": ListenerNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def stop_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.STOP_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)
    except Exception as exc:
        raise InternalServerErrorError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    if listener.status.state != ListenerState.RUNNING:
        raise ListenerNotRunningError(
            message="The listener cannot be stopped because it is not running.",
        )

    try:
        await listener.stop_listener()
    except FrameworkListenerStopError as exc:
        raise ListenerStopError(message=exc.message, detail=exc.detail)

    return SuccessResponseModel()


@router.post(
    "/{listener_id}/cancel",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerCancellationError(message="string").to_pydantic_model()},
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        409: {"model": ListenerNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def cancel_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CANCEL_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)

    if listener.status.state != ListenerState.RUNNING:
        raise ListenerNotRunningError(
            message="The listener cannot be cancelled because it is not running.",
        )

    try:
        await listener.cancel_listener()
    except FrameworkListenerCancellationError as exc:
        raise ListenerCancellationError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerErrorError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.patch(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        409: {"model": ListenerAlreadyRunningAPIError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidListenerParameterNameError(
                parameter_name="string",
            ).to_pydantic_model()
            | InvalidListenerParameterValueError(
                parameter_name="string",
                parameter_value="string",
                exception=Exception("string"),
            ).to_pydantic_model(),
        },
        500: {
            "model": ListenerTemplateResolutionError(
                listener_type=example_listener_type,
            ).to_pydantic_model(),
        },
    },
)
def update_listener_by_listener_id(
    listener_id: str,
    # The only update-able listener attributes are its name, description and parameters
    # within the listener. Note that when instantiating the listener through its
    # listener template the options of a listener template are responsible for setting
    # both the name and endpoint string of the listener. Hence, when updating the
    # parameters of a listener, the name and endpoint strings are also updated by
    # running those update values through the listener template. However, it is
    # possible to update the name of a listener independently of the parameters by
    # simply not specifying any parameters when PUTing. But if the parameters are
    # present they will override the name string even if it was specified in the
    # request.
    name: Annotated[str, Body] | None = None,
    description: Annotated[str, Body] | None = None,
    parameters: Annotated[dict[str, Any], Body] | None = None,
) -> ListenerModel:
    try:
        if name is not None:
            listeners_service.update_listener_name_by_listener_id(
                listener_id=listener_id,
                name=name,
            )
        if description is not None:
            listeners_service.update_listener_name_by_listener_id(
                listener_id=listener_id,
                name=name,
            )
        if parameters is not None:
            try:
                listeners_service.update_listener_name_by_listener_id(
                    listener_id=listener_id,
                    name=name,
                )
            # ListenerTemplateResolutionError is only ever raised when a programmer
            # error is made.
            except ListenerTemplateResolutionError:
                raise InternalServerErrorError
            except ListenerAlreadyRunningServiceError:
                raise ListenerAlreadyRunningAPIError
            except InvalidListenerParameterNameServiceError:
                pass
            except InvalidListenerParameterValueServiceError:
                pass
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)

    listener = listeners_service.get_listener_by_listener_id(listener_id=listener_id)
    return ListenerModel(**listener.to_json())


@router.delete(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": ListenerNotFoundAPIError(listener_id="string").to_pydantic_model(),
        },
        409: {"model": ListenerAlreadyRunningAPIError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def delete_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listeners_service.remove_listener_by_listener_id(listener_id=listener_id)
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError(listener_id=listener_id)
    except ListenerAlreadyRunningAPIError:
        pass

    return SuccessResponseModel()
