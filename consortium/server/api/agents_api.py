from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    agents_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions import (
    agents_service_exceptions as svc_excs,
)

# import (
#     AgentNotFoundError as svc_excs.AgentNotFoundError,
#     AgentResultNotFoundError as svc_excs.AgentResultNotFoundError,
#     AgentTaskingOptionValidationError as svc_excs.AgentTaskingOptionValidationError,
#     AgentTaskingRequiredOptionValueNotSetError as svc_excs.AgentTaskingRequiredOptionValueNotSetError,
#     AgentTaskNotFoundError as svc_excs.AgentTaskNotFoundError,
# )
from consortium.server.models.agent_models import (
    AgentModel,
    AgentResultModel,
    AgentTaskModel,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

agents_service = server_singletons.agents_service
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
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/queued",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/running",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/completed",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/results",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/results/success",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/results/fail",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model()
            | api_excs.AgentTaskNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentTaskNotFoundError(
                    task_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.get(
    "/{agent_id}/results/{result_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model()
            | api_excs.AgentResultNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentResultNotFoundError(
                    result_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.AgentResultNotFoundError as exc:
        raise api_excs.AgentResultNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.post(
    "/{agent_id}/tasks",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": api_excs.AgentTaskingOptionValueValidationError.from_consortium_exception(
                consortium_exception=svc_excs.AgentTaskingOptionValidationError(
                    agent_str="string",
                    error_message="string",
                ),
            ).to_pydantic_model()
            | api_excs.AgentTaskingRequiredOptionValueNotSetError.from_consortium_exception(
                consortium_exception=svc_excs.AgentTaskingRequiredOptionValueNotSetError(
                    agent_str="string",
                    error_message="string",
                ),
            ).to_pydantic_model(),
        },
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.AgentTaskingOptionValidationError as exc:
        raise api_excs.AgentTaskingOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.AgentTaskingRequiredOptionValueNotSetError as exc:
        raise api_excs.AgentTaskingRequiredOptionValueNotSetError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return task


@router.patch(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {
            "model": api_excs.AgentNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def update_agent_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_AGENT_BY_AGENT_ID,
            ),
        ),
    ],
    # The only update-able agent attributes are its name, and description within the
    # agent.
    name: Annotated[str, Body(embed=True)] = None,
    description: Annotated[str, Body(embed=True)] = None,
) -> AgentModel:
    try:
        if name is not None:
            await agents_service.update_agent_name_by_agent_id(
                agent_id=agent_id,
                name=name,
            )
        if description is not None:
            await agents_service.update_agent_description_by_agent_id(
                agent_id=agent_id,
                description=description,
            )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    # If the agent ID provided is invalid AND no parameters were passed to be
    # patched it is possible for the above block to execute and not raise an exception.
    # So we still need to check for that here.
    try:
        agent = agents_service.get_agent_by_agent_id(
            agent_id=agent_id,
        )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return AgentModel(**agent.to_json())


@router.delete(
    "/{agent_id}/tasks/queued/{task_id}",
    responses={
        200: {"model": AgentTaskModel},
        404: {
            "model": api_excs.AgentTaskNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.AgentTaskNotFoundError(task_id="string"),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return SuccessResponseModel()
