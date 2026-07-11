from typing import Annotated

from fastapi import APIRouter, Body, Depends
from pydantic import UUID4, JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions import (
    listeners_framework_exceptions,
)
from consortium.server.exceptions.api_exceptions import (
    listeners_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.service_exceptions import (
    listeners_service_exceptions as consortium_exceptions,
)
from consortium.server.models.listener_models import ListenerModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/listeners",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Listeners API"],
)

_listeners_service = server_singletons.listeners_service
_listener_templates_service = server_singletons.listener_templates_service

_listener_not_found_error = api_excs.ListenerNotFoundError.from_consortium_exception(
    consortium_exceptions.ListenerNotFoundError(listener_id="<listener_id>"),
)
_listener_already_running_error = (
    api_excs.ListenerAlreadyRunningError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerAlreadyRunningError(
            listener_str="<listener_string>",
        ),
    )
)
_listener_start_error = api_excs.ListenerStartError.from_consortium_exception(
    consortium_exception=listeners_framework_exceptions.ListenerStartError(
        listener_str="<listener_string>",
        error_message="<error_message>",
        detail={"<key>": "<value>"},
    ),
)
_listener_not_running_error = (
    api_excs.ListenerNotRunningError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerNotRunningError(
            listener_str="<listener_string>",
        ),
    )
)
_listener_stop_error = api_excs.ListenerStopError.from_consortium_exception(
    consortium_exception=listeners_framework_exceptions.ListenerStopError(
        listener_str="<listener_string>",
        error_message="<error_message>",
        detail={"<key>": "<value>"},
    ),
)
_invalid_listener_parameter_name_error = (
    api_excs.InvalidListenerParameterNameError.from_consortium_exception(
        consortium_exception=consortium_exceptions.InvalidListenerParameterNameError(
            listener_str="<listener_str>",
            parameter_name="<parameter_name>",
        ),
    )
)
_invalid_listener_parameter_value_error = (
    api_excs.InvalidListenerParameterValueError.from_consortium_exception(
        consortium_exception=consortium_exceptions.InvalidListenerParameterValueError(
            listener_str="<listener_str>",
            parameter_name="<parameter_name>",
            parameter_value="<parameter_value>",
            error_message="<error_message>",
        ),
    )
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
)
_invalid_uuid_error = InvalidUUIDError(
    resource_name="listener", uuid_value="<uuid_value>"
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
        for listener in _listeners_service.get_all_listeners()
    ]


@router.get(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_LISTENER_BY_LISTENER_ID),
        ),
    ],
) -> ListenerModel:
    try:
        return ListenerModel(
            **_listeners_service.get_listener_by_listener_id(listener_id).to_json(),
        )
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.post(
    "/{listener_id}/start",
    status_code=202,
    responses={
        202: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        409: {
            "model": _listener_already_running_error.to_pydantic_model()
            | _listener_start_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def start_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.START_LISTENER_BY_LISTENER_ID)),
    ],
) -> ListenerModel:
    try:
        listener = await _listeners_service.start_listener_by_listener_id(
            listener_id=listener_id
        )
    except listeners_framework_exceptions.ListenerStartError as exc:
        raise api_excs.ListenerStartError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listeners_framework_exceptions.ListenerAlreadyRunningError as exc:
        raise api_excs.ListenerAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None

    return ListenerModel(**listener.to_json())


@router.post(
    "/{listener_id}/stop",
    status_code=202,
    responses={
        202: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        409: {
            "model": _listener_not_running_error.to_pydantic_model()
            | _listener_stop_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def stop_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.STOP_LISTENER_BY_LISTENER_ID)),
    ],
) -> ListenerModel:
    try:
        listener = await _listeners_service.stop_listener_by_listener_id(
            listener_id=listener_id
        )
    except listeners_framework_exceptions.ListenerStopError as exc:
        raise api_excs.ListenerStopError(
            message=exc.message, detail=exc.detail
        ) from None
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listeners_framework_exceptions.ListenerNotRunningError as exc:
        raise api_excs.ListenerNotRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None

    return ListenerModel(**listener.to_json())


@router.post(
    "/{listener_id}/cancel",
    status_code=202,
    responses={
        202: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        409: {
            "model": _listener_not_running_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def cancel_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CANCEL_LISTENER_BY_LISTENER_ID)),
    ],
) -> ListenerModel:
    try:
        listener = await _listeners_service.cancel_listener_by_listener_id(
            listener_id=listener_id
        )
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listeners_framework_exceptions.ListenerNotRunningError as exc:
        raise api_excs.ListenerNotRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None

    return ListenerModel(**listener.to_json())


@router.patch(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        409: {"model": _listener_already_running_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _invalid_listener_parameter_name_error.to_pydantic_model()
            | _invalid_listener_parameter_value_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def update_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_LISTENER_BY_LISTENER_ID,
            ),
        ),
    ],
    name: Annotated[str | None, Body(embed=True)] = None,
    description: Annotated[str | None, Body(embed=True)] = None,
    parameters: Annotated[dict[str, JsonValue] | None, Body(embed=True)] = None,
) -> ListenerModel:
    try:
        listener = _listeners_service.update_listener_by_listener_id(
            listener_id=listener_id,
            name=name,
            description=description,
            parameters=parameters,
        )
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listeners_framework_exceptions.ListenerAlreadyRunningError as exc:
        raise api_excs.ListenerAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_exceptions.InvalidListenerParameterNameError as exc:
        raise api_excs.InvalidListenerParameterNameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_exceptions.InvalidListenerParameterValueError as exc:
        raise api_excs.InvalidListenerParameterValueError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return ListenerModel(**listener.to_json())


@router.delete(
    "/{listener_id}",
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        409: {"model": _listener_already_running_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def delete_listener_by_listener_id(
    listener_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_LISTENER_BY_LISTENER_ID)),
    ],
) -> None:
    try:
        _listeners_service.remove_listener_by_listener_id(listener_id=listener_id)
    except consortium_exceptions.ListenerNotFoundError as exc:
        raise api_excs.ListenerNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listeners_framework_exceptions.ListenerAlreadyRunningError as exc:
        raise api_excs.ListenerAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
