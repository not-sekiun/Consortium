from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.server_exceptions import (
    AgentGeneratorAlreadyBuildingError,
    AgentGeneratorNotFoundError,
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)

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


@router.post(
    "/all",
    responses={
        201: {"model": AgentGeneratorModel},
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


@router.post(
    "/{agent_generator_id}",
    responses={
        201: {"model": AgentGeneratorModel},
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


@router.delete(
    "/{agent_generator_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorAlreadyBuildingError().to_pydantic_model()},
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
        raise AgentGeneratorNotFoundError

    if agent_generator.status.state == AgentGeneratorState.BUILDING:
        raise AgentGeneratorAlreadyBuildingError
    agent_generators_service.remove_agent_generator(agent_generator)
    return SuccessResponseModel()
