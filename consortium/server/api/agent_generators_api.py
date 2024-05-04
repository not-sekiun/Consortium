from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.agent_generators_api_exceptions import (
    AgentGeneratorAlreadyRunningError,
    AgentGeneratorCancellationError,
    AgentGeneratorNotFoundError,
    AgentGeneratorNotRunningError,
    AgentGeneratorStartError,
    AgentGeneratorStopError,
)
from consortium.server.exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.framework.exceptions import (
    AgentGeneratorCancellationError as FrameworkAgentGeneratorCancellationError,
)
from consortium.server.framework.exceptions import (
    AgentGeneratorStartError as FrameworkAgentGeneratorStartError,
)
from consortium.server.framework.exceptions import (
    AgentGeneratorStopError as FrameworkAgentGeneratorStopError,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
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
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agent_generators_service = server_singletons.agent_generators_service


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
        for agent_generator in agent_generators_service.get_all_agent_generators()
    ]


@router.get(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
    },
    status_code=201,
)
def get_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
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
            **agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id,
            ).to_json(),
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)


@router.post(
    "/{agent_generator_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": AgentGeneratorStartError().to_pydantic_model()},
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def start_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
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
        agent_generator = (
            agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
            )
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)

    if agent_generator.status.state == AgentGeneratorState.RUNNING:
        raise AgentGeneratorAlreadyRunningError(
            message="The agent generator cannot be started because it is already "
            "running",
        )

    try:
        await agent_generator.start_agent_generator()
    except FrameworkAgentGeneratorStartError as exc:
        raise AgentGeneratorStartError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.post(
    "/{agent_generator_id}/stop",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": AgentGeneratorStopError().to_pydantic_model()},
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def stop_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
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
        agent_generator = (
            agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
            )
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)

    if agent_generator.status.state != AgentGeneratorState.RUNNING:
        raise AgentGeneratorNotRunningError(
            message="The agent generator cannot be stopped because it is not running",
        )

    try:
        await agent_generator.stop_agent_generator()
    except FrameworkAgentGeneratorStopError as exc:
        raise AgentGeneratorStopError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.post(
    "/{agent_generator_id}/cancel",
    responses={
        200: {"model": SuccessResponseModel},
        400: {
            "model": AgentGeneratorCancellationError(
                message="string",
            ).to_pydantic_model(),
        },
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def cancel_listener_by_listener_id(
    agent_generator_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CANCEL_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        agent_generator = (
            agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
            )
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)

    if agent_generator.status.state != AgentGeneratorState.RUNNING:
        raise AgentGeneratorNotRunningError(
            message=(
                "The agent generator cannot be cancelled because it is not running."
            ),
        )

    try:
        await agent_generator.cancel_agent_generator()
    except FrameworkAgentGeneratorCancellationError as exc:
        raise AgentGeneratorCancellationError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.delete(
    "/{agent_generator_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorAlreadyRunningError().to_pydantic_model()},
    },
)
def delete_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_LISTENER_BY_LISTENER_ID)),
    ],
):
    try:
        agent_generator = (
            agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id,
            )
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id=agent_generator_id)

    if agent_generator.status.state == AgentGeneratorState.RUNNING:
        raise AgentGeneratorAlreadyRunningError
    agent_generators_service.remove_agent_generator(agent_generator)
    return SuccessResponseModel()
