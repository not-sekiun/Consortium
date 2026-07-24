from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

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
)
from consortium.server.exceptions.service_exceptions import (
    listeners_service_exceptions as consortium_exceptions,
)
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.request_body_models import UpdateListenerRequestBodyModel
from consortium.server.models.union_response_models import (
    ListenerStartConflictErrorResponse,
    ListenerStopConflictErrorResponse,
    ListenerUpdateValidationErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
)
from consortium.server.utils import MAX_EVENT_LOG_LIMIT, clamp_event_log_limit

router = APIRouter(
    prefix="/api/listeners",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Listeners"],
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
_listener_not_running_error = (
    api_excs.ListenerNotRunningError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerNotRunningError(
            listener_str="<listener_string>",
        ),
    )
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
    # Collection responses omit per-resource event log entries so the total response
    # stays bounded regardless of how many listeners exist. Use the detail endpoint to
    # page a specific listener's event log via limit/offset.
    return [
        ListenerModel(**listener.to_json(include_event_log_entries=False))
        for listener in _listeners_service.get_all_listeners()
    ]


@router.get(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {
            "model": _listener_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
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
    limit: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Maximum number of event log entries to return. Values above "
                f"{MAX_EVENT_LOG_LIMIT} are capped to {MAX_EVENT_LOG_LIMIT}."
            ),
        ),
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in the event log. Negative values offset from the end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> ListenerModel:
    try:
        return ListenerModel(
            **_listeners_service.get_listener_by_listener_id(listener_id).to_json(
                limit=clamp_event_log_limit(limit), offset=offset
            ),
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
        409: {"model": ListenerStartConflictErrorResponse},
        422: {"model": RequestValidationErrorResponse},
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
        409: {"model": ListenerStopConflictErrorResponse},
        422: {"model": RequestValidationErrorResponse},
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
        422: {"model": RequestValidationErrorResponse},
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
        422: {"model": ListenerUpdateValidationErrorResponse},
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
    update_listener_request_body: UpdateListenerRequestBodyModel,
) -> ListenerModel:
    name = update_listener_request_body.name
    description = update_listener_request_body.description
    parameters = update_listener_request_body.parameters

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
        422: {"model": RequestValidationErrorResponse},
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
