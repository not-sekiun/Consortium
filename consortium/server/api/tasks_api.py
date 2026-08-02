from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    tasks_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.service_exceptions import (
    tasks_service_exceptions as svc_excs,
)
from consortium.server.models.task_models import TaskModel, TaskState
from consortium.server.models.union_response_models import (
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.utils import MAX_EVENT_LOG_LIMIT, clamp_event_log_limit

router = APIRouter(
    prefix="/api/tasks",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Tasks"],
)

_tasks_service = server_singletons.tasks_service

_task_not_found_error = api_excs.TaskNotFoundError.from_consortium_exception(
    consortium_exception=svc_excs.TaskNotFoundError(task_id="string")
)
_task_not_deletable_error = api_excs.TaskNotDeletableError.from_consortium_exception(
    consortium_exception=svc_excs.TaskNotDeletableError(
        task_str="'<command>' (<task_id>)",
        state=TaskState.RUNNING,
    )
)


@router.get(
    "/all",
    responses={
        200: {"model": list[TaskModel]},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def get_all_tasks(
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS))
    ],
    agent_id: UUID4 | None = None,
    status: TaskState | None = None,
) -> list[TaskModel]:
    tasks = _tasks_service.get_all_tasks(agent_id=agent_id, status=status)
    # Collection responses omit event entries so response size is bounded. The detail
    # endpoint provides limit/offset pagination for an individual task's event log.
    return [
        TaskModel(**task.to_json(include_event_log_entries=False)) for task in tasks
    ]


@router.get(
    "/{task_id}",
    responses={
        200: {"model": TaskModel},
        404: {"model": _task_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def get_task_by_task_id(
    task_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_AGENT_TASK_BY_TASK_ID))
    ],
    limit: Annotated[
        int,
        Query(
            gt=0,
            description=(
                "Maximum number of task events to return. Values above "
                f"{MAX_EVENT_LOG_LIMIT} are capped to {MAX_EVENT_LOG_LIMIT}."
            ),
        ),
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description=(
                "Starting position in the task event log. Negative values offset from "
                "the end. If None, the last limit entries are returned."
            )
        ),
    ] = None,
) -> TaskModel:
    try:
        task = _tasks_service.get_task_by_task_id(task_id=task_id)
    except svc_excs.TaskNotFoundError as exc:
        raise api_excs.TaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return TaskModel(**task.to_json(limit=clamp_event_log_limit(limit), offset=offset))


@router.delete(
    "/{task_id}",
    status_code=204,
    responses={
        204: {},
        404: {"model": _task_not_found_error.to_pydantic_model()},
        409: {"model": _task_not_deletable_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def delete_task_by_task_id(
    task_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_AGENT_TASK_BY_TASK_ID)),
    ],
) -> None:
    try:
        await _tasks_service.delete_task_by_task_id(task_id=task_id)
    except svc_excs.TaskNotFoundError as exc:
        raise api_excs.TaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.TaskNotDeletableError as exc:
        raise api_excs.TaskNotDeletableError.from_consortium_exception(
            consortium_exception=exc
        ) from None
