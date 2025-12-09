from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    listeners_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions import (
    listeners_service_exceptions as svc_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.listener_models import ListenerModel
from consortium.server.objects.example_objects import example_listener_type
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

listeners_service = server_singletons.listeners_service
listener_templates_service = server_singletons.listener_templates_service
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
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                svc_excs.ListenerNotFoundError(listener_id="string"),
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
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )


@router.post(
    "/{listener_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                svc_excs.ListenerNotFoundError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {
            "model": api_excs.ListenerAlreadyRunningError.from_service_exception(
                service_exception=svc_excs.ListenerAlreadyRunningError(),
            ).to_pydantic_model()
            | api_excs.ListenerStartError.from_service_exception(
                service_exception=svc_excs.ListenerStartError(
                    message="string",
                    detail={"string": "string"},
                ),
                # detail={"string": "string"},
            ).to_pydantic_model(),
        },
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
    except svc_excs.ListenerStartError as exc:
        raise api_excs.ListenerStartError.from_service_exception(
            service_exception=exc,
            detail=exc.detail,
        )
    except svc_excs.ListenerAlreadyRunningError as exc:
        raise api_excs.ListenerAlreadyRunningError.from_service_exception(
            service_exception=exc,
        )
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )
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
        404: {
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                service_exception=svc_excs.ListenerNotFoundError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {
            "model": api_excs.ListenerNotRunningError.from_service_exception(
                service_exception=svc_excs.ListenerNotRunningError(),
            ).to_pydantic_model()
            | api_excs.ListenerStopError.from_service_exception(
                service_exception=svc_excs.ListenerStopError(
                    message="string",
                    detail={"string": "string"},
                ),
                detail={"string": "string"},
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
    except svc_excs.ListenerStopError as exc:
        raise api_excs.ListenerStopError(message=exc.message, detail=exc.detail)
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )
    except svc_excs.ListenerNotRunningError as exc:
        raise api_excs.ListenerNotRunningError.from_service_exception(
            service_exception=exc,
        )
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
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                service_exception=svc_excs.ListenerNotFoundError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {
            "model": api_excs.ListenerNotRunningError.from_service_exception(
                service_exception=svc_excs.ListenerNotRunningError(),
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
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )
    except svc_excs.ListenerNotRunningError as exc:
        raise api_excs.ListenerNotRunningError.from_service_exception(
            service_exception=exc,
        )
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
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                service_exception=svc_excs.ListenerNotFoundError(listener_id="string"),
            ).to_pydantic_model(),
        },
        409: {"model": api_excs.ListenerAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | api_excs.InvalidListenerParameterNameError.from_service_exception(
                service_exception=svc_excs.InvalidListenerParameterNameError(
                    parameter_name="string",
                    listener_str="string",
                ),
            ).to_pydantic_model()
            | api_excs.InvalidListenerParameterValueError.from_service_exception(
                service_exception=svc_excs.InvalidListenerParameterValueError(
                    parameter_name="string",
                    parameter_value="string",
                    listener_str="string",
                    validation_error_message="string",
                ),
            ).to_pydantic_model(),
        },
        500: {
            "model": api_excs.ListenerTemplateResolutionError(
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
            # api_excs.ListenerTemplateResolutionError is only ever raised when a programmer
            # error is made. The service will raise an AssertionError to demonstrate
            # this, which will be caught and reraised as a
            # api_excs.ListenerTemplateResolutionError on the REST API side.
            except AssertionError:
                raise api_excs.ListenerTemplateResolutionError
            except svc_excs.ListenerAlreadyRunningError as exc:
                raise api_excs.ListenerAlreadyRunningError.from_service_exception(
                    service_exception=exc,
                )
            except svc_excs.InvalidListenerParameterNameError as exc:
                raise api_excs.InvalidListenerParameterNameError.from_service_exception(
                    service_exception=exc,
                )
            except svc_excs.InvalidListenerParameterValueError as exc:
                raise api_excs.InvalidListenerParameterValueError.from_service_exception(
                    service_exception=exc,
                )
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )

    # If the listener ID provided is invalid AND no parameters were passed to be
    # patched it is possible for the above block to execute and not raise an exception.
    # So we still need to check for that here.
    try:
        listener = listeners_service.get_listener_by_listener_id(
            listener_id=listener_id,
        )
    except svc_excs.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=exc,
        )

    return ListenerModel(**listener.to_json())


@router.delete(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": api_excs.ListenerNotFoundError.from_service_exception(
                service_exception=svc_excs.ListenerNotFoundError(
                    listener_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {"model": api_excs.ListenerAlreadyRunningError().to_pydantic_model()},
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
    except svc_excs.ListenerNotFoundError:
        raise api_excs.ListenerNotFoundError.from_service_exception(
            service_exception=svc_excs.ListenerNotFoundError(
                listener_id="string",
            ),
        )
    except svc_excs.ListenerAlreadyRunningError as exc:
        raise api_excs.ListenerAlreadyRunningError.from_service_exception(
            service_exception=exc,
        )

    return SuccessResponseModel()
