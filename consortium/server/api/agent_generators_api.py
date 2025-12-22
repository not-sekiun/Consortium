from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    agent_generators_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.consortium_exceptions import (
    agent_generators_consortium_exceptions as consortium_excs,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.example_objects import example_agent_type
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agent-generators",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agent Generators API"],
)

_agent_generators_service = server_singletons.agent_generators_service
_agent_templates_service = server_singletons.agent_templates_service

_agent_generator_not_found_error = (
    api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentGeneratorNotFoundError(
            agent_generator_id="<agent_generator_id>"
        )
    )
)
_agent_generator_already_running_error = (
    api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentGeneratorAlreadyRunningError(
            agent_generator_str="<agent_generator_str>"
        )
    )
)
_agent_generator_not_running_error = (
    api_excs.AgentGeneratorNotRunningError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentGeneratorNotRunningError(
            agent_generator_str="<agent_generator_str>"
        )
    )
)
_agent_generator_start_error = (
    api_excs.AgentGeneratorStartError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentGeneratorStartError(
            agent_generator_str="<agent_generator_str>",
            error_message="<error_message>",
            detail={"<key>": "<value>"},
        )
    )
)
_agent_generator_stop_error = (
    api_excs.AgentGeneratorStopError.from_consortium_exception(
        consortium_exception=consortium_excs.AgentGeneratorStopError(
            agent_generator_str="<agent_generator_str>",
            error_message="<error_message>",
            detail={"<key>": "<value>"},
        )
    )
)
_invalid_agent_generator_parameter_name_error = (
    api_excs.InvalidAgentGeneratorParameterNameError.from_consortium_exception(
        consortium_exception=consortium_excs.InvalidAgentGeneratorParameterNameError(
            parameter_name="<parameter_name>", agent_generator="<agent_generator>"
        )
    )
)
_invalid_agent_generator_parameter_value_error = (
    api_excs.InvalidAgentGeneratorParameterValueError.from_consortium_exception(
        consortium_exception=consortium_excs.InvalidAgentGeneratorParameterValueError(
            agent_generator_str="<agent_generator>",
            parameter_name="<parameter_name>",
            parameter_value="<parameter_value>",
            error_message="<error_message>",
        )
    )
)
_agent_template_resolution_error = api_excs.AgentTemplateResolutionError(
    agent_type=example_agent_type
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}]
)


@router.get(
    "/all",
    responses={
        200: {"model": AgentGeneratorModel},
    },
    status_code=201,
)
def get_all_agent_generators(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_GENERATORS)),
    ],
) -> list[AgentGeneratorModel]:
    return [
        AgentGeneratorModel(**agent_generator.to_json())
        for agent_generator in _agent_generators_service.get_all_agent_generators()
    ]


@router.get(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        422: {"model": _unprocessable_entity_error.to_pydantic_model()},
    },
    status_code=201,
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
) -> AgentGeneratorModel:
    try:
        return AgentGeneratorModel(
            **_agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id,
            ).to_json(),
        )
    except consortium_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.post(
    "/{agent_generator_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {
            "model": _agent_generator_already_running_error.to_pydantic_model()
            | _agent_generator_start_error.to_pydantic_model()
        },
        422: {"model": _unprocessable_entity_error.to_pydantic_model()},
    },
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
) -> SuccessResponseModel:
    try:
        await _agent_generators_service.start_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except consortium_excs.AgentGeneratorStartError as exc:
        raise api_excs.AgentGeneratorStartError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorAlreadyRunningError as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorNotFoundError as exc:
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

    return SuccessResponseModel()


@router.post(
    "/{agent_generator_id}/stop",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {
            "model": _agent_generator_not_running_error.to_pydantic_model()
            | _agent_generator_stop_error.to_pydantic_model()
        },
        422: {"model": _unprocessable_entity_error.to_pydantic_model()},
    },
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
) -> SuccessResponseModel:
    try:
        await _agent_generators_service.stop_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except consortium_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorStopError as exc:
        raise api_excs.AgentGeneratorStopError.from_consortium_exception(
            consortium_exception=exc
        ) from None
    except consortium_excs.AgentGeneratorNotRunningError as exc:
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

    return SuccessResponseModel()


@router.post(
    "/{agent_generator_id}/cancel",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_not_running_error.to_pydantic_model()},
        422: {"model": _unprocessable_entity_error.to_pydantic_model()},
    },
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
) -> SuccessResponseModel:
    try:
        await _agent_generators_service.cancel_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except consortium_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorNotRunningError as exc:
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

    return SuccessResponseModel()


@router.patch(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_already_running_error.to_pydantic_model()},
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model()
            | _invalid_agent_generator_parameter_name_error.to_pydantic_model()
            | _invalid_agent_generator_parameter_value_error.to_pydantic_model()
        },
        500: {"model": _agent_template_resolution_error.to_pydantic_model()},
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
    name: Annotated[str, Body(embed=True)] = None,
    description: Annotated[str, Body(embed=True)] = None,
    parameters: Annotated[dict[str, Any], Body(embed=True)] = None,
) -> AgentGeneratorModel:
    try:
        agent_generator = (
            _agent_generators_service.update_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
                name=name,
                description=description,
                parameters=parameters,
            )
        )
    except consortium_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorAlreadyRunningError as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.InvalidAgentGeneratorParameterNameError as exc:
        raise api_excs.InvalidAgentGeneratorParameterNameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.InvalidAgentGeneratorParameterValueError as exc:
        raise api_excs.InvalidAgentGeneratorParameterValueError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return AgentGeneratorModel(**agent_generator.to_json())


@router.delete(
    "/{agent_generator_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _agent_generator_not_found_error.to_pydantic_model()},
        409: {"model": _agent_generator_already_running_error.to_pydantic_model()},
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
):
    try:
        _agent_generators_service.remove_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except consortium_excs.AgentGeneratorNotFoundError as exc:
        raise api_excs.AgentGeneratorNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.AgentGeneratorAlreadyRunningError as exc:
        raise api_excs.AgentGeneratorAlreadyRunningError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return SuccessResponseModel()
