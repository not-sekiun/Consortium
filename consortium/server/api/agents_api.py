from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.agents_api_exceptions import (
    AgentNotFoundError as AgentNotFoundAPIError,
    AgentResultNotFoundError as AgentResultNotFoundAPIError,
    AgentTaskNotFoundError as AgentTaskNotFoundAPIError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError as AgentNotFoundServiceError,
    AgentResultNotFoundError as AgentResultNotFoundServiceError,
    AgentTaskNotFoundError as AgentTaskNotFoundServiceError,
)
from consortium.server.models.agent_models import (
    AgentModel,
    AgentResultModel,
    AgentTaskModel,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agents",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Agents API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agents_service = server_singletons.agents_service


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentModel]},
    },
)
def get_all_agents(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENTS)),
    ],
):
    return [AgentModel(**agent.to_json()) for agent in agents_service.get_all_agents()]


@router.get(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def get_agent_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_AGENT_BY_AGENT_ID),
        ),
    ],
):
    try:
        return AgentModel(
            **agents_service.get_agent_by_agent_id(agent_id).to_json(),
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/tasks",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_agent_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return agents_service.get_all_agent_tasks_by_agent_id(agent_id=agent_id)
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/tasks/queued",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_queued_agent_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return agents_service.get_all_queued_agent_tasks_by_agent_id(agent_id=agent_id)
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/tasks/running",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_running_agent_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return agents_service.get_all_running_agent_tasks_by_agent_id(agent_id=agent_id)
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/tasks/completed",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_completed_agent_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return agents_service.get_all_completed_agent_tasks_by_agent_id(
            agent_id=agent_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/results",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_agent_results_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentResultModel]:
    try:
        return agents_service.get_all_agent_results_by_agent_id(agent_id=agent_id)
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/results/success",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_successful_agent_results_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentResultModel]:
    try:
        return agents_service.get_all_successful_agent_results_by_agent_id(
            agent_id=agent_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/results/fail",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
    },
)
def get_all_failed_agent_results_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentResultModel]:
    try:
        return agents_service.get_all_failed_agent_results_by_agent_id(
            agent_id=agent_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model()
            | AgentTaskNotFoundAPIError.from_service_exception(
                service_exception=AgentTaskNotFoundServiceError(
                    task_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
)
def get_agent_tasks_by_agent_id_and_task_id(
    agent_id: str,
    task_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> AgentTaskModel:
    try:
        return agents_service.get_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id,
            task_id=task_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)
    except AgentTaskNotFoundServiceError as exc:
        raise AgentTaskNotFoundAPIError.from_service_exception(service_exception=exc)


@router.get(
    "/{agent_id}/results/{result_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model()
            | AgentResultNotFoundAPIError.from_service_exception(
                service_exception=AgentResultNotFoundServiceError(
                    result_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
)
def get_agent_result_by_agent_id_and_result_id(
    agent_id: str,
    result_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID),
        ),
    ],
) -> AgentResultModel:
    try:
        return agents_service.get_agent_result_by_agent_id_and_result_id(
            agent_id=agent_id,
            result_id=result_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)
    except AgentResultNotFoundServiceError as exc:
        raise AgentResultNotFoundAPIError.from_service_exception(service_exception=exc)


@router.post(
    "/{agent_id}/tasks",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": AgentNotFoundAPIError.from_service_exception(
                service_exception=AgentNotFoundServiceError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {},
    },
)
async def task_agent_by_agent_id(
    agent_id: str,
    command: Annotated[str, Body()],
    arguments: Annotated[dict[str, Any] | list, Body()],
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.TASK_AGENT_BY_AGENT_ID),
        ),
    ],
) -> AgentTaskModel:
    try:
        task = await agents_service.task_agent_by_agent_id(
            agent_id=agent_id,
            command=command,
            arguments=arguments,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)

    return task


@router.delete(
    "/{agent_id}/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": AgentTaskNotFoundAPIError.from_service_exception(
                service_exception=AgentTaskNotFoundServiceError(task_id="string"),
            ).to_pydantic_model(),
        },
    },
)
async def delete_queued_agent_task_by_agent_id_and_task_id(
    agent_id: str,
    task_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.DELETE_AGENT_TASK_BY_TASK_ID),
        ),
    ],
) -> SuccessResponseModel:
    try:
        await agents_service.delete_queued_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id,
            task_id=task_id,
        )
    except AgentNotFoundServiceError as exc:
        raise AgentNotFoundAPIError.from_service_exception(service_exception=exc)
    except AgentTaskNotFoundServiceError as exc:
        raise AgentTaskNotFoundAPIError.from_service_exception(service_exception=exc)

    return SuccessResponseModel()
