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
from consortium.server.models.agent_task_and_result_models import (
    AgentResultModel,
    AgentResultStatus,
    AgentTaskAPIResponseModel,
    AgentTaskModel,
    AgentTaskProgressLogAPIResponseModel,
    AgentTaskStatus,
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


def _convert_agent_task_model_to_api_response_model(
    task: AgentTaskModel,
    progress_limit: int = 10,
    progress_offset: int | None = None,
) -> AgentTaskAPIResponseModel:
    progress_log = task.progress_log
    total_count = len(progress_log)

    if total_count == 0:
        filtered_entries = []
    else:
        # Get min and max sequence numbers
        sequences = [entry.sequence for entry in progress_log]
        min_seq = min(sequences)
        max_seq = max(sequences)

        # If offset is None, return the tail (entries with highest sequence numbers)
        if progress_offset is None:
            # Get entries with the highest sequence numbers, up to progress_limit
            start_seq = max(min_seq, max_seq - progress_limit + 1)
            filtered_entries = [
                entry for entry in progress_log if entry.sequence >= start_seq
            ]
            # Sort by sequence and take the last progress_limit entries
            filtered_entries = sorted(filtered_entries, key=lambda e: e.sequence)[
                -progress_limit:
            ]
        # Handle negative offset (from max sequence)
        elif progress_offset < 0:
            start_seq = max(min_seq, max_seq + progress_offset + 1)
            end_seq = start_seq + progress_limit - 1
            filtered_entries = [
                entry
                for entry in progress_log
                if start_seq <= entry.sequence <= end_seq
            ]
            filtered_entries = sorted(filtered_entries, key=lambda e: e.sequence)
        else:
            # Filter entries where sequence >= progress_offset
            start_seq = progress_offset
            end_seq = progress_offset + progress_limit - 1
            filtered_entries = [
                entry
                for entry in progress_log
                if start_seq <= entry.sequence <= end_seq
            ]
            filtered_entries = sorted(filtered_entries, key=lambda e: e.sequence)

    return AgentTaskAPIResponseModel(
        task_id=task.task_id,
        command=task.command,
        arguments=task.arguments,
        status=task.status,
        current_progress=task.current_progress,
        progress_log=AgentTaskProgressLogAPIResponseModel(
            total_count=total_count,
            entries=filtered_entries,
        ),
        datetime_created=task.datetime_created,
        datetime_started=task.datetime_started,
    )


def _convert_agent_task_models_to_api_response_models(
    tasks: list[AgentTaskModel],
    progress_limit: int = 10,
    progress_offset: int | None = None,
) -> list[AgentTaskAPIResponseModel]:
    return [
        _convert_agent_task_model_to_api_response_model(
            task, progress_limit, progress_offset
        )
        for task in tasks
    ]


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
        200: {"model": list[AgentTaskAPIResponseModel]},
    },
)
def get_all_agent_tasks(
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS))
    ],
    status: AgentTaskStatus | None = None,
    progress_limit: Annotated[
        int, Query(gt=0, description="Maximum number of progress log entries to return")
    ] = 10,
    progress_offset: Annotated[
        int | None,
        Query(
            description="Starting position in progress log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> list[AgentTaskAPIResponseModel]:
    tasks = _agents_service.get_all_agent_tasks(status=status)
    return _convert_agent_task_models_to_api_response_models(
        tasks, progress_limit, progress_offset
    )


@router.get(
    "/tasks/{task_id}",
    responses={
        200: {"model": AgentTaskAPIResponseModel},
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
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS))
    ],
    progress_limit: Annotated[
        int, Query(gt=0, description="Maximum number of progress log entries to return")
    ] = 10,
    progress_offset: Annotated[
        int | None,
        Query(
            description="Starting position in progress log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskAPIResponseModel:
    try:
        task = _agents_service.get_agent_task_by_task_id(task_id=task_id)
    except consortium_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return _convert_agent_task_model_to_api_response_model(
        task=task,
        progress_limit=progress_limit,
        progress_offset=progress_offset,
    )


@router.get(
    "/results",
    responses={
        200: {"model": list[AgentResultModel]},
    },
)
def get_all_agent_results(
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS))
    ],
    status: AgentResultStatus | None = None,
) -> list[AgentResultModel]:
    return _agents_service.get_all_agent_results(status=status)


@router.get(
    "/results/{result_id}",
    responses={
        200: {"model": AgentResultModel},
        404: {"model": _agent_result_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_result_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_result_by_result_id(
    _: Annotated[
        None, Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS))
    ],
    result_id: UUID4,
) -> AgentResultModel:
    try:
        return _agents_service.get_agent_result_by_result_id(result_id=result_id)
    except consortium_excs.AgentResultIDNotFoundError as exc:
        raise api_excs.AgentResultNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/tasks",
    responses={
        200: {"model": list[AgentTaskAPIResponseModel]},
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
    status: AgentTaskStatus | None = None,
    progress_limit: Annotated[
        int, Query(gt=0, description="Maximum number of progress log entries to return")
    ] = 10,
    progress_offset: Annotated[
        int | None,
        Query(
            description="Starting position in progress log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> list[AgentTaskAPIResponseModel]:
    try:
        tasks = _agents_service.get_all_agent_tasks_by_agent_id(
            agent_id=agent_id, status=status
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None

    return _convert_agent_task_models_to_api_response_models(
        tasks=tasks,
        progress_limit=progress_limit,
        progress_offset=progress_offset,
    )


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
        200: {"model": AgentTaskAPIResponseModel},
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
    progress_limit: Annotated[
        int, Query(gt=0, description="Maximum number of progress log entries to return")
    ] = 10,
    progress_offset: Annotated[
        int | None,
        Query(
            description="Starting position in progress log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskAPIResponseModel:
    try:
        task = _agents_service.get_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id, task_id=task_id
        )
        return _convert_agent_task_model_to_api_response_model(
            task, progress_limit, progress_offset
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentTaskNotFoundError as exc:
        raise api_excs.AgentTaskNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.get(
    "/{agent_id}/results",
    responses={
        200: {"model": list[AgentResultModel]},
        404: {"model": _agent_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_all_agent_results_by_agent_id(
    agent_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID)),
    ],
    status: AgentResultStatus | None = None,
) -> list[AgentResultModel]:
    try:
        return _agents_service.get_all_agent_results_by_agent_id(
            agent_id=agent_id, status=status
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


# TODO: Consider adding a get result by task ID too
@router.get(
    "/{agent_id}/results/{result_id}",
    responses={
        200: {"model": AgentResultModel},
        404: {
            "model": _agent_not_found_error.to_pydantic_model()
            | _agent_result_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_agent_uuid_error.to_pydantic_model()
            | _invalid_result_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_result_by_agent_id_and_result_id(
    agent_id: UUID4,
    result_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID)
        ),
    ],
) -> AgentResultModel:
    try:
        return _agents_service.get_agent_result_by_agent_id_and_result_id(
            agent_id=agent_id, result_id=result_id
        )
    except consortium_excs.AgentNotFoundError as exc:
        raise api_excs.AgentNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentResultIDNotFoundError as exc:
        raise api_excs.AgentResultNotFoundError.from_consortium_exception(
            consortium_exception=exc
        ) from None


@router.post(
    "/{agent_id}/tasks",
    responses={
        200: {"model": AgentTaskAPIResponseModel},
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
    progress_limit: Annotated[
        int, Query(gt=0, description="Maximum number of progress log entries to return")
    ] = 10,
    progress_offset: Annotated[
        int | None,
        Query(
            description="Starting position in progress log. Negative values offset from end. If None and limit is provided, returns the tail (last N entries)."
        ),
    ] = None,
) -> AgentTaskAPIResponseModel:
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

    return _convert_agent_task_model_to_api_response_model(
        task, progress_limit, progress_offset
    )


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
    name: Annotated[str, Body(embed=True)] = None,
    description: Annotated[str, Body(embed=True)] = None,
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
    responses={
        200: {"model": SuccessResponseModel},
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
) -> SuccessResponseModel:
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

    return SuccessResponseModel()
