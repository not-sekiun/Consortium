from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

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
from consortium.server.exceptions.framework_exceptions import (
    agents_framework_exceptions as agent_framework_excs,
)
from consortium.server.exceptions.service_exceptions import (
    agents_service_exceptions as svc_excs,
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
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agents API"],
)

_agents_service = server_singletons.agents_service

_agent_capability_option_value_validation_framework_error = (
    agent_framework_excs.AgentCapabilityOptionValueValidationError(
        agent_str="<agent_str>",
        option_name="<option_name>",
        option_value="<option_value>",
        error_message="<error_message>",
    )
)
_missing_required_agent_capability_option_framework_error = (
    agent_framework_excs.MissingRequiredAgentCapabilityOptionError(
        agent_str="<agent_str>",
        option_name="<option_name>",
        agent_capability_name="<agent_capability_name>",
    )
)
_agent_capability_option_not_found_framework_error = (
    agent_framework_excs.AgentCapabilityOptionNotFoundError(
        agent_str="<agent_str>",
        option_name="<option_name>",
        command="<command>",
        agent_type_str="<agent_type_str>",
    )
)
_agent_not_found_error = api_excs.AgentNotFoundError.from_consortium_exception(
    consortium_exception=svc_excs.AgentNotFoundError(agent_id="string"),
)
_agent_task_not_found_error = api_excs.AgentTaskNotFoundError.from_consortium_exception(
    consortium_exception=svc_excs.AgentTaskNotFoundError(task_id="string"),
)
_agent_result_not_found_error = (
    api_excs.AgentResultNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.AgentResultNotFoundError(result_id="string"),
    )
)
_agent_capability_option_value_validation_framework_error = (
    api_excs.AgentCapabilityOptionValueValidationError.from_consortium_exception(
        consortium_exception=svc_excs.AgentCapabilityOptionValueValidationError(
            message=_agent_capability_option_value_validation_framework_error.message,
            detail=_agent_capability_option_value_validation_framework_error.detail,
        ),
    )
)
_agent_capability_option_not_found_error = (
    api_excs.AgentCapabilityOptionNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.AgentCapabilityOptionNotFoundError(
            message=_agent_capability_option_not_found_framework_error.message,
            detail=_agent_capability_option_not_found_framework_error.detail,
        ),
    )
)
_missing_required_agent_capability_option_framework_error = (
    api_excs.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
        consortium_exception=svc_excs.MissingRequiredAgentCapabilityOptionError(
            message=_missing_required_agent_capability_option_framework_error.message,
            detail=_missing_required_agent_capability_option_framework_error.detail,
        ),
    )
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
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
    return [AgentModel(**agent.to_json()) for agent in _agents_service.get_all_agents()]


@router.get(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
            **_agents_service.get_agent_by_agent_id(agent_id).to_json(),
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
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_all_agent_tasks_by_agent_id(agent_id=agent_id)
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/queued",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
def get_all_queued_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return _agents_service.get_all_queued_tasks_by_agent_id(agent_id=agent_id)
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/running",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_all_running_agent_tasks_by_agent_id(
            agent_id=agent_id
        )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks/completed",
    responses={
        200: {"model": list[AgentTaskModel]},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
def get_all_completed_tasks_by_agent_id(
    agent_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID),
        ),
    ],
) -> list[AgentTaskModel]:
    try:
        return _agents_service.get_all_completed_tasks_by_agent_id(
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
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_all_agent_results_by_agent_id(agent_id=agent_id)
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/results/success",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_all_successful_agent_results_by_agent_id(
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
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_all_failed_agent_results_by_agent_id(
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
            "model": _agent_not_found_error.to_pydantic_model()
            | _agent_task_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_agent_task_by_agent_id_and_task_id(
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
            "model": _agent_not_found_error.to_pydantic_model()
            | _agent_result_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        return _agents_service.get_agent_result_by_agent_id_and_result_id(
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
            "model": _agent_not_found_error.to_pydantic_model()
            | _agent_capability_option_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _agent_capability_option_value_validation_framework_error.to_pydantic_model()
            | _missing_required_agent_capability_option_framework_error.to_pydantic_model(),
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
        task = await _agents_service.task_agent_by_agent_id(
            agent_id=agent_id,
            command=command,
            arguments=arguments,
        )
    except svc_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except svc_excs.AgentCapabilityOptionNotFoundError as exc:
        raise api_excs.AgentCapabilityOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.AgentCapabilityOptionValueValidationError as exc:
        raise api_excs.AgentCapabilityOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.MissingRequiredAgentCapabilityOptionError as exc:
        raise api_excs.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return task


@router.patch(
    "/{agent_id}",
    responses={
        200: {"model": AgentModel},
        404: {
            "model": _agent_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
            await _agents_service.update_agent_name_by_agent_id(
                agent_id=agent_id,
                name=name,
            )
        if description is not None:
            await _agents_service.update_agent_description_by_agent_id(
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
        agent = _agents_service.get_agent_by_agent_id(
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
            "model": _agent_task_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model(),
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
        await _agents_service.delete_queued_agent_task_by_agent_id_and_task_id(
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
