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
    InvalidListenerParameterNameError as InvalidListenerParameterNameAPIError,
    InvalidListenerParameterValueError as InvalidListenerParameterValueAPIError,
    ListenerAlreadyRunningError as ListenerAlreadyRunningAPIError,
    ListenerNotFoundError as ListenerNotFoundAPIError,
    ListenerNotRunningError as ListenerNotRunningAPIError,
    ListenerStartError as ListenerStartAPIError,
    ListenerStopError as ListenerStopAPIError,
    ListenerTemplateResolutionError,
)
from consortium.server.exceptions.service_exceptions.listeners_service_exceptions import (
    InvalidListenerParameterNameError as InvalidListenerParameterNameServiceError,
    InvalidListenerParameterValueError as InvalidListenerParameterValueServiceError,
    ListenerAlreadyRunningError as ListenerAlreadyRunningServiceError,
    ListenerNotFoundError as ListenerNotFoundServiceError,
    ListenerNotRunningError as ListenerNotRunningServiceError,
    ListenerStartError as ListenerStartServiceError,
    ListenerStopError as ListenerStopServiceError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.listener_models import ListenerModel
from consortium.server.objects.example_objects import example_listener_type
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
) -> list[ListenerModel]:
    return [
        ListenerModel(**listener.to_json())
        for listener in listeners_service.get_all_listeners()
    ]


@router.get(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {
            "model": ListenerNotFoundAPIError.from_service_exception(
                ListenerNotFoundServiceError(listener_id="string"),
            ).to_pydantic_model(),
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
) -> ListenerModel:
    try:
        return ListenerModel(
            **listeners_service.get_listener_by_listener_id(listener_id).to_json(),
        )
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(service_exception=exc)


@router.post(
    "/{listener_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {
            "model": ListenerStartAPIError.from_service_exception(
                service_exception=ListenerStartServiceError(
                    message="string",
                    detail={"string": "string"},
                ),
                detail={"string": "string"},
            ).to_pydantic_model(),
        },
        404: {
            "model": ListenerNotFoundAPIError.from_service_exception(
                ListenerNotFoundServiceError(listener_id="string"),
            ).to_pydantic_model(),
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
        await listeners_service.start_listener_by_listener_id(listener_id=listener_id)
    except ListenerStartServiceError as exc:
        raise ListenerStartAPIError.from_service_exception(
            service_exception=exc,
            detail=exc.detail,
        )
    except ListenerAlreadyRunningServiceError as exc:
        raise ListenerAlreadyRunningAPIError.from_service_exception(
            service_exception=exc,
        )
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(service_exception=exc)
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
        400: {
            "model": ListenerStopAPIError.from_service_exception(
                service_exception=ListenerStopServiceError(
                    message="string",
                    detail={"string": "string"},
                ),
                detail={"string": "string"},
            ).to_pydantic_model(),
        },
        404: {
            "model": ListenerNotFoundAPIError.from_service_exception(
                service_exception=ListenerNotFoundServiceError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {
            "model": ListenerNotRunningAPIError.from_service_exception(
                service_exception=ListenerNotRunningServiceError(),
            ).to_pydantic_model(),
        },
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
        await listeners_service.stop_listener_by_listener_id(listener_id=listener_id)
    except ListenerStopServiceError as exc:
        raise ListenerStopAPIError(message=exc.message, detail=exc.detail)
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(service_exception=exc)
    except ListenerNotRunningServiceError as exc:
        raise ListenerNotRunningAPIError.from_service_exception(service_exception=exc)
    except Exception as exc:
        raise InternalServerErrorError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.post(
    "/{listener_id}/cancel",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": ListenerNotFoundAPIError.from_service_exception(
                service_exception=ListenerNotFoundServiceError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {
            "model": ListenerNotRunningAPIError.from_service_exception(
                service_exception=ListenerNotRunningServiceError(),
            ).to_pydantic_model(),
        },
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
        await listeners_service.cancel_listener_by_listener_id(listener_id=listener_id)
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(service_exception=exc)
    except ListenerNotRunningServiceError as exc:
        raise ListenerNotRunningAPIError.from_service_exception(service_exception=exc)
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
            "model": ListenerNotFoundAPIError.from_service_exception(
                service_exception=ListenerNotFoundServiceError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {"model": ListenerAlreadyRunningAPIError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidListenerParameterNameAPIError.from_service_exception(
                service_exception=InvalidListenerParameterNameServiceError(
                    parameter_name="string",
                    listener="string",
                ),
            ).to_pydantic_model()
            | InvalidListenerParameterValueAPIError.from_service_exception(
                service_exception=InvalidListenerParameterValueServiceError(
                    parameter_name="string",
                    parameter_value="string",
                    listener="string",
                    validation_error_message="string",
                ),
            ).to_pydantic_model(),
        },
        500: {
            "model": ListenerTemplateResolutionError(
                listener_type=example_listener_type,
            ).to_pydantic_model(),
        },
    },
)
async def update_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_LISTENER_BY_LISTENER_ID,
            ),
        ),
    ],
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
    name: Annotated[str, Body(embed=True)] = None,
    description: Annotated[str, Body(embed=True)] = None,
    parameters: Annotated[dict[str, Any], Body(embed=True)] = None,
) -> ListenerModel:
    try:
        if name is not None:
            await listeners_service.update_listener_name_by_listener_id(
                listener_id=listener_id,
                name=name,
            )
        if description is not None:
            await listeners_service.update_listener_description_by_listener_id(
                listener_id=listener_id,
                description=description,
            )
        if parameters is not None:
            try:
                await listeners_service.update_listener_parameters_by_listener_id(
                    listener_id=listener_id,
                    parameters=parameters,
                )
            # ListenerTemplateResolutionError is only ever raised when a programmer
            # error is made. The service wi ll raise an AssertionError to demonstrate
            # this, which will be caught and reraised as a
            # ListenerTemplateResolutionError on the REST API side.
            except AssertionError:
                raise ListenerTemplateResolutionError
            except ListenerAlreadyRunningServiceError as exc:
                raise ListenerAlreadyRunningAPIError.from_service_exception(
                    service_exception=exc,
                )
            except InvalidListenerParameterNameServiceError as exc:
                raise InvalidListenerParameterNameAPIError.from_service_exception(
                    service_exception=exc,
                )
            except InvalidListenerParameterValueServiceError as exc:
                raise InvalidListenerParameterValueAPIError.from_service_exception(
                    service_exception=exc,
                )
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )

    # If the listener ID provided is invalid AND no parameters were passed to be
    # patched it is possible for the above block to execute and not raise an exception.
    # So we still need to check for that here.
    try:
        listener = listeners_service.get_listener_by_listener_id(
            listener_id=listener_id,
        )
    except ListenerNotFoundServiceError as exc:
        raise ListenerNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )

    return ListenerModel(**listener.to_json())


@router.delete(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": ListenerNotFoundAPIError.from_service_exception(
                service_exception=ListenerNotFoundServiceError(
                    listener_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {"model": ListenerAlreadyRunningAPIError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def delete_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        await listeners_service.remove_listener_by_listener_id(listener_id=listener_id)
    except ListenerNotFoundServiceError:
        raise ListenerNotFoundAPIError.from_service_exception(
            service_exception=ListenerNotFoundServiceError(
                listener_id="string",
            ),
        )
    except ListenerAlreadyRunningServiceError as exc:
        raise ListenerAlreadyRunningAPIError.from_service_exception(
            service_exception=exc,
        )

    return SuccessResponseModel()
