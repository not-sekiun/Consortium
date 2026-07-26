from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions import (
    agent_generators_framework_exceptions,
)
from consortium.server.exceptions.api_exceptions import (
    agent_generators_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.service_exceptions import (
    agent_generators_service_exceptions as svc_excs,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.request_body_models import (
    UpdateAgentGeneratorRequestBodyModel,
)
from consortium.server.models.union_response_models import (
    AgentGeneratorStartConflictErrorResponse,
    AgentGeneratorStopConflictErrorResponse,
    AgentGeneratorUpdateValidationErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
)
from consortium.server.utils import MAX_EVENT_LOG_LIMIT, clamp_event_log_limit

router = APIRouter(
    prefix="/api/agent-generators",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agent Generators"],
)

_agent_generators_service = server_singletons.agent_generators_service
_agent_templates_service = server_singletons.agent_templates_service

_agent_generator_not_found_error = (
    api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.AgentGeneratorNotFoundError(
            agent_generator_id="<agent_generator_id>"
        )
    )
)
_agent_generator_already_running_error = api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorAlreadyRunningError(
        component_str="<agent_generator_str>"
    )
)
_agent_generator_not_running_error = api_excs.AgentGeneratorNotRunningError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorNotRunningError(
        component_str="<agent_generator_str>"
    )
)
_invalid_uuid_error = InvalidUUIDError(
    resource_name="agent generator", uuid_value="<uuid_value>"
)


@router.get(
    "/all",
    responses={
        200: {"model": AgentGeneratorModel},
    },
)
def get_all_agent_generators(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_GENERATORS)),
    ],
) -> list[AgentGeneratorModel]:
    # Collection responses omit per-resource event log entries so the total response
    # stays bounded regardless of how many generators exist. Use the detail endpoint to
    # page a specific generator's event log via limit/offset.
    return [
        AgentGeneratorModel(**agent_generator.to_json(include_event_log_entries=False))
        for agent_generator in _agent_generators_service.get_all_agent_generators()
    ]


@router.get(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
def get_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.READ_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
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
) -> AgentGeneratorModel:
    try:
        return AgentGeneratorModel(
            **_agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id,
            ).to_json(limit=clamp_event_log_limit(limit), offset=offset),
        )
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.post(
    "/{agent_generator_id}/start",
    responses={
        202: {},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": AgentGeneratorStartConflictErrorResponse},
        422: {"model": RequestValidationErrorResponse},
    },
    status_code=202,
)
async def start_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.START_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> None:
    try:
        await _agent_generators_service.start_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except agent_generators_framework_exceptions.AgentGeneratorStartError as exc:
        raise api_excs.AgentGeneratorStartError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        agent_generators_framework_exceptions.AgentGeneratorAlreadyRunningError
    ) as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None


@router.post(
    "/{agent_generator_id}/stop",
    responses={
        202: {},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": AgentGeneratorStopConflictErrorResponse},
        422: {"model": RequestValidationErrorResponse},
    },
    status_code=202,
)
async def stop_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.STOP_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> None:
    try:
        await _agent_generators_service.stop_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except agent_generators_framework_exceptions.AgentGeneratorStopError as exc:
        raise api_excs.AgentGeneratorStopError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except agent_generators_framework_exceptions.AgentGeneratorNotRunningError as exc:
        raise api_excs.AgentGeneratorNotRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None


@router.post(
    "/{agent_generator_id}/cancel",
    responses={
        202: {},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_not_running_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
    status_code=202,
)
async def cancel_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.CANCEL_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> None:
    try:
        await _agent_generators_service.cancel_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except agent_generators_framework_exceptions.AgentGeneratorNotRunningError as exc:
        raise api_excs.AgentGeneratorNotRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from None


@router.patch(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_already_running_error.to_pydantic_model()},
        422: {"model": AgentGeneratorUpdateValidationErrorResponse},
    },
)
async def update_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
    update_agent_generator_request_body: UpdateAgentGeneratorRequestBodyModel,
) -> AgentGeneratorModel:
    name = update_agent_generator_request_body.name
    description = update_agent_generator_request_body.description
    parameters = update_agent_generator_request_body.parameters

    try:
        agent_generator = (
            _agent_generators_service.update_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
                name=name,
                description=description,
                parameters=parameters,
            )
        )
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        agent_generators_framework_exceptions.AgentGeneratorAlreadyRunningError
    ) as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.InvalidAgentGeneratorParameterNameError as exc:
        raise api_excs.InvalidAgentGeneratorParameterNameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.InvalidAgentGeneratorParameterValueError as exc:
        raise api_excs.InvalidAgentGeneratorParameterValueError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return AgentGeneratorModel(**agent_generator.to_json())


@router.delete(
    "/{agent_generator_id}",
    status_code=204,
    responses={
        204: {},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_already_running_error.to_pydantic_model()},
        422: {"model": _invalid_uuid_error.to_pydantic_model()},
    },
)
async def delete_agent_generator_by_agent_generator_id(
    agent_generator_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.DELETE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> None:
    try:
        _agent_generators_service.remove_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except svc_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        agent_generators_framework_exceptions.AgentGeneratorAlreadyRunningError
    ) as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
