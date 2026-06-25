from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    agents_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.consortium_exceptions import (
    agents_consortium_exceptions as consortium_excs,
)
from consortium.server.models.agent_models import (
    AgentModel,
)
from consortium.server.models.agent_task_models import (
    AgentTaskModel,
    AgentTaskState,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agents",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agents API"],
)

_agents_service = server_singletons.agents_service

_agent_not_found_error = api_excs.AgentNotFoundError.from_consortium_exception(
    consortium_exception=consortium_excs.AgentNotFoundError(agent_id="string"),
)
_agent_task_not_found_error = api_excs.AgentTaskNotFoundError.from_consortium_exception(
    consortium_exception=consortium_excs.AgentTaskNotFoundError(task_id="string"),
)
_agent_result_not_found_error = (
    api_excs.AgentResultNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentResultIDNotFoundError(
            result_id="string"
        ),
    )
)
_agent_capability_option_value_validation_error = (
    api_excs.AgentCapabilityOptionValueValidationError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentCapabilityOptionValueValidationError(
            agent_str="<agent_str>",
            option_name="<option_str>",
            option_value="<option_value>",
            error_message="<error_message>",
        ),
    )
)
_agent_capability_option_not_found_error = (
    api_excs.AgentCapabilityOptionNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentCapabilityOptionNotFoundError(
            agent_str="<agent_str>",
            option_name="<option_str>",
            command="<command>",
            agent_type_str="<agent_type_str>",
        ),
    )
)
_missing_required_agent_capability_option_error = (
    api_excs.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
        consortium_exception=consortium_excs.MissingRequiredAgentCapabilityOptionError(
            agent_str="<agent_str>",
            option_name="<option_str>",
            agent_capability_name="<agent_capability_name>",
        )
    )
)
_agent_capability_not_found_error = (
    api_excs.AgentCapabilityNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentCapabilityNotFoundError(
            command="<command>",
            agent_str="<agent_str>",
            agent_type_str="<agent_type_str>",
        ),
    )
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
)
_invalid_agent_uuid_error = InvalidUUIDError(
    resource_name="agent", uuid_value="<uuid_value>"
)
_invalid_task_uuid_error = InvalidUUIDError(
    resource_name="task", uuid_value="<uuid_value>"
)
_invalid_result_uuid_error = InvalidUUIDError(
    resource_name="result", uuid_value="<uuid_value>"
)


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentModel]},
    },
)
def get_all_agents(
    _: Annotated[None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENTS))],
):
    return [AgentModel(**agent.to_json()) for agent in _agents_service.get_all_agents()]


@router.get(
    "/tasks",
    responses={
        200: {"model": list[AgentTaskModel]},
    },
)
def get_all_agent_tasks(
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS))
    ],
    status: AgentTaskState | None = None,
    limit: Annotated[
        int, Query(gt=0, description="Maximum number of task events to return")
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in task event log. Negative values offset from the end. If offset is `None` and `limit` is provided, returns the last `N` entries."
        ),
    ] = None,
) -> list[AgentTaskModel]:
    tasks = _agents_service.get_all_agent_tasks(status=status)
    return [
        AgentTaskModel(**task.to_json(limit=limit, offset=offset)) for task in tasks
    ]


@router.get(
    "/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {"model": _agent_task_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_task_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_task_by_task_id(
    task_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_AGENT_TASK_BY_TASK_ID))
    ],
    limit: Annotated[
        int, Query(gt=0, description="Maximum number of task events to return")
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in task events log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskModel:
    try:
        task = _agents_service.get_agent_task_by_task_id(task_id=task_id)
    except consortium_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return AgentTaskModel(**task.to_json(limit=limit, offset=offset))


@router.get(
    "/{agent_id}/tasks",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_all_agent_tasks_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID)),
    ],
    status: AgentTaskState | None = None,
    limit: Annotated[
        int, Query(gt=0, description="Maximum number of task events to return")
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in task events log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> list[AgentTaskModel]:
    try:
        tasks = _agents_service.get_all_agent_tasks_by_agent_id(
            agent_id=agent_id, status=status
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return [
        AgentTaskModel(**task.to_json(limit=limit, offset=offset)) for task in tasks
    ]


@router.get(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_AGENT_BY_AGENT_ID))
    ],
):
    try:
        return AgentModel(**_agents_service.get_agent_by_agent_id(agent_id).to_json())
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": _agent_not_found_error.to_pydantic_model()
            | _agent_task_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _invalid_task_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_tasks_by_agent_id_and_task_id(
    agent_id: UUID4,
    task_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID)),
    ],
    limit: Annotated[
        int, Query(gt=0, description="Maximum number of task events to return")
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in task events log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskModel:
    try:
        task = _agents_service.get_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id, task_id=task_id
        )
        return AgentTaskModel(**task.to_json(limit=limit, offset=offset))
        # return _convert_agent_task_model_to_api_response_model(task, limit, offset)
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.post(
    "/{agent_id}/tasks",
    responses={
        200: {"model": AgentTaskModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _agent_capability_option_value_validation_error.to_pydantic_model()
            | _missing_required_agent_capability_option_error.to_pydantic_model()
            | _agent_capability_option_not_found_error.to_pydantic_model()
            | _agent_capability_not_found_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def task_agent_by_agent_id(
    agent_id: UUID4,
    command: Annotated[str, Body()],
    arguments: Annotated[dict[str, Any] | list, Body()],
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.TASK_AGENT_BY_AGENT_ID))
    ],
    limit: Annotated[
        int, Query(gt=0, description="Maximum number of task events to return")
    ] = 10,
    offset: Annotated[
        int | None,
        Query(
            description="Starting position in task events log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskModel:
    try:
        task = await _agents_service.task_agent_by_agent_id(
            agent_id=agent_id, command=command, arguments=arguments
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentCapabilityNotFoundError as exc:
        raise api_excs.AgentCapabilityNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentCapabilityOptionNotFoundError as exc:
        raise api_excs.AgentCapabilityOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentCapabilityOptionValueValidationError as exc:
        raise api_excs.AgentCapabilityOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.MissingRequiredAgentCapabilityOptionError as exc:
        raise api_excs.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return AgentTaskModel(**task.to_json(limit=limit, offset=offset))


@router.patch(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def update_agent_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.UPDATE_AGENT_BY_AGENT_ID))
    ],
    name: Annotated[str | None, Body(embed=True)] = None,
    description: Annotated[str | None, Body(embed=True)] = None,
) -> AgentModel:
    try:
        agent = _agents_service.update_agent_by_agent_id(
            agent_id=agent_id, name=name, description=description
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return AgentModel(**agent.to_json())


@router.delete(
    "/{agent_id}/tasks/queued/{task_id}",
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _agent_task_not_found_error.to_pydantic_model()
            | _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _invalid_task_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def delete_queued_agent_task_by_agent_id_and_task_id(
    agent_id: UUID4,
    task_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_AGENT_TASK_BY_TASK_ID)),
    ],
) -> None:
    try:
        await _agents_service.delete_queued_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id, task_id=task_id
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
