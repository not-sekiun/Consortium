from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    agents_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.object_exceptions import (
    agent_object_exceptions as obj_excs,
)
from consortium.server.exceptions.service_exceptions import (
    agents_service_exceptions as svc_excs,
)
from consortium.server.models.agent_models import (
    AgentModel,
)
from consortium.server.models.request_body_models import (
    AgentTaskRequestBodyModel,
    UpdateAgentRequestBodyModel,
)
from consortium.server.models.task_models import TaskModel
from consortium.server.models.union_response_models import (
    AgentTaskingValidationErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
)
from consortium.server.utils import MAX_EVENT_LOG_LIMIT, clamp_event_log_limit

router = APIRouter(
    prefix="/api/agents",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agents"],
)

_agents_service = server_singletons.agents_service

_agent_not_found_error = api_excs.AgentNotFoundError.from_consortium_exception(
    consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
)


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentModel]},
    },
)
async def get_all_agents(
    _: Annotated[None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENTS))],
):
    return [AgentModel(**agent.to_json()) for agent in _agents_service.get_all_agents()]


@router.get(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def get_agent_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_AGENT_BY_AGENT_ID))
    ],
):
    try:
        return AgentModel(**_agents_service.get_agent_by_agent_id(agent_id).to_json())
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.post(
    "/{agent_id}/tasks",
    responses={
        200: {"model": TaskModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {"model": AgentTaskingValidationErrorResponse},
    },
)
async def task_agent_by_agent_id(
    agent_id: UUID4,
    agent_task_request_body: AgentTaskRequestBodyModel,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.TASK_AGENT_BY_AGENT_ID))
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
            description="Starting position in task events log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> TaskModel:
    command = agent_task_request_body.command
    arguments = agent_task_request_body.arguments

    try:
        task = await _agents_service.task_agent_by_agent_id(
            agent_id=agent_id, command=command, arguments=arguments
        )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except obj_excs.AgentCapabilityNotFoundError as exc:
        raise api_excs.AgentCapabilityNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except obj_excs.AgentCapabilityOptionNotFoundError as exc:
        raise api_excs.AgentCapabilityOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except obj_excs.AgentCapabilityOptionValueValidationError as exc:
        raise api_excs.AgentCapabilityOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except obj_excs.MissingRequiredAgentCapabilityOptionError as exc:
        raise api_excs.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except obj_excs.AgentCapabilityValidatingFunctionError as exc:
        raise api_excs.AgentCapabilityValidatingFunctionError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return TaskModel(**task.to_json(limit=clamp_event_log_limit(limit), offset=offset))


@router.patch(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def update_agent_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.UPDATE_AGENT_BY_AGENT_ID))
    ],
    update_agent_request_body: UpdateAgentRequestBodyModel,
) -> AgentModel:
    name = update_agent_request_body.name
    description = update_agent_request_body.description

    try:
        agent = _agents_service.update_agent_by_agent_id(
            agent_id=agent_id, name=name, description=description
        )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return AgentModel(**agent.to_json())


@router.delete(
    "/{agent_id}",
    status_code=204,
    responses={
        204: {},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
async def delete_agent_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.DELETE_AGENT_BY_AGENT_ID))
    ],
) -> None:
    try:
        await _agents_service.delete_agent_by_agent_id(agent_id=agent_id)
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
