from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.agent_generators_api_exceptions import (
    AgentGeneratorAlreadyRunningError as AgentGeneratorAlreadyRunningAPIError,
    AgentGeneratorNotFoundError as AgentGeneratorNotFoundAPIError,
    AgentGeneratorNotRunningError as AgentGeneratorNotRunningAPIError,
    AgentGeneratorStartError as AgentGeneratorStartAPIError,
    AgentGeneratorStopError as AgentGeneratorStopAPIError,
    AgentTemplateResolutionError,
    InvalidAgentGeneratorParameterNameError as InvalidAgentGeneratorParameterNameAPIError,
    InvalidAgentGeneratorParameterValueError as InvalidAgentGeneratorParameterValueAPIError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions import (
    AgentGeneratorAlreadyRunningError as AgentGeneratorAlreadyRunningServiceError,
    AgentGeneratorNotFoundError as AgentGeneratorNotFoundServiceError,
    AgentGeneratorNotRunningError as AgentGeneratorNotRunningServiceError,
    AgentGeneratorStartError as AgentGeneratorStartServiceError,
    AgentGeneratorStopError as AgentGeneratorStopServiceError,
    InvalidAgentGeneratorParameterNameError as InvalidAgentGeneratorParameterNameServiceError,
    InvalidAgentGeneratorParameterValueError as InvalidAgentGeneratorParameterValueServiceError,
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
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Agent Generators API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agent_generators_service = server_singletons.agent_generators_service
agent_templates_service = server_singletons.agent_templates_service


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
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
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
    except AgentGeneratorNotFoundServiceError as exc:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )


@router.post(
    "/{agent_generator_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {
            "model": AgentGeneratorStartAPIError.from_service_exception(
                service_exception=AgentGeneratorStartServiceError(
                    message="string",
                    detail={"string": "string"},
                ),
                detail={"string": "string"},
            ).to_pydantic_model(),
        },
        404: {
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {
            "model": AgentGeneratorAlreadyRunningAPIError.from_service_exception(
                service_exception=AgentGeneratorAlreadyRunningServiceError(),
            ).to_pydantic_model(),
        },
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
        agent_generators_service.start_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except AgentGeneratorStartServiceError as exc:
        raise AgentGeneratorStartAPIError.from_service_exception(
            service_exception=exc,
            detail=exc.detail,
        )
    except AgentGeneratorAlreadyRunningServiceError as exc:
        raise AgentGeneratorAlreadyRunningAPIError.from_service_exception(
            service_exception=exc,
        )
    except AgentGeneratorNotFoundServiceError as exc:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except Exception as exc:
        raise InternalServerErrorError(
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
        400: {
            "model": AgentGeneratorStopAPIError.from_service_exception(
                service_exception=AgentGeneratorStopServiceError(
                    message="string",
                    detail={"string": "string"},
                ),
                detail={"string": "string"},
            ).to_pydantic_model(),
        },
        404: {
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {
            "model": AgentGeneratorNotRunningAPIError.from_service_exception(
                service_exception=AgentGeneratorNotRunningServiceError(),
            ).to_pydantic_model(),
        },
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
                UserPermissions.STOP_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> SuccessResponseModel:
    try:
        agent_generators_service.stop_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except AgentGeneratorNotFoundServiceError as exc:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except AgentGeneratorStopServiceError as exc:
        raise AgentGeneratorStopAPIError.from_service_exception(service_exception=exc)
    except AgentGeneratorNotRunningServiceError as exc:
        raise AgentGeneratorNotRunningAPIError.from_service_exception(
            service_exception=exc,
        )
    except Exception as exc:
        raise InternalServerErrorError(
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
        404: {
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {
            "model": AgentGeneratorNotRunningAPIError.from_service_exception(
                service_exception=AgentGeneratorNotRunningServiceError(),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def cancel_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
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
        agent_generators_service.cancel_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except AgentGeneratorNotFoundServiceError as exc:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except AgentGeneratorNotRunningServiceError as exc:
        raise AgentGeneratorNotRunningAPIError.from_service_exception(
            service_exception=exc,
        )
    except Exception as exc:
        raise InternalServerErrorError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.patch(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {
            "model": AgentGeneratorAlreadyRunningAPIError.from_service_exception(
                service_exception=AgentGeneratorAlreadyRunningServiceError(),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidAgentGeneratorParameterNameAPIError.from_service_exception(
                service_exception=InvalidAgentGeneratorParameterNameServiceError(
                    parameter_name="string",
                    agent_generator="string",
                ),
            ).to_pydantic_model()
            | InvalidAgentGeneratorParameterValueAPIError.from_service_exception(
                service_exception=InvalidAgentGeneratorParameterValueServiceError(
                    agent_generator="string",
                    parameter_name="string",
                    parameter_value="string",
                    validation_error_message="string",
                ),
            ).to_pydantic_model(),
        },
        500: {
            "model": AgentTemplateResolutionError(
                agent_type=example_agent_type,
            ).to_pydantic_model(),
        },
    },
)
def update_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
    # The only update-able agent generator attributes are its name, description and
    # parameters within the agent generator. Note that when instantiating the agent
    # generator through its agent template the options of an agent template are
    # responsible for setting the name of the agent generator. Hence, when updating the
    # parameters of an agent generator, the name is also updated by running those update
    # values through the agent template. However, it is possible to update the name of
    # an agent generator independently of the parameters by simply not specifying any
    # parameters when PUTing. But if the parameters are present they will override the
    # name string even if it was specified in the request.
    name: Annotated[str, Body] | None = None,
    description: Annotated[str, Body] | None = None,
    parameters: Annotated[dict[str, Any], Body] | None = None,
) -> AgentGeneratorModel:
    try:
        if name is not None:
            agent_generators_service.update_agent_generator_name_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
                name=name,
            )
        if description is not None:
            agent_generators_service.update_agent_generator_name_by_agent_generator_id(
                agent_generator_id=agent_generator_id,
                name=name,
            )
        if parameters is not None:
            try:
                agent_generators_service.update_agent_generator_name_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    name=name,
                )
            # AgentTemplateResolutionError is only ever raised when a programmer
            # error is made. The service will raise an AssertionError to demonstrate
            # this, which will be caught and reraised as a
            # AgentGeneratorTemplateResolutionError on the REST API side.
            except AssertionError:
                raise AgentTemplateResolutionError
            except AgentGeneratorAlreadyRunningServiceError as exc:
                raise AgentGeneratorAlreadyRunningAPIError.from_service_exception(
                    service_exception=exc,
                )
            except InvalidAgentGeneratorParameterNameServiceError as exc:
                raise InvalidAgentGeneratorParameterNameAPIError.from_service_exception(
                    service_exception=exc,
                )
            except InvalidAgentGeneratorParameterValueServiceError as exc:
                raise InvalidAgentGeneratorParameterValueAPIError.from_service_exception(
                    service_exception=exc,
                )
    except AgentGeneratorNotFoundServiceError:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=AgentGeneratorNotFoundServiceError(
                agent_generator_id="string",
            ),
        )

    agent_generator = (
        agent_generators_service.get_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    )
    return AgentGeneratorModel(**agent_generator.to_json())


@router.delete(
    "/{agent_generator_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": AgentGeneratorNotFoundAPIError.from_service_exception(
                service_exception=AgentGeneratorNotFoundServiceError(
                    agent_generator_id="string",
                ),
            ).to_pydantic_model(),
        },
        409: {
            "model": AgentGeneratorAlreadyRunningAPIError.from_service_exception(
                service_exception=AgentGeneratorAlreadyRunningServiceError(),
            ).to_pydantic_model(),
        },
    },
)
def delete_agent_generator_by_agent_generator_id(
    agent_generator_id: str,
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
        agent_generators_service.remove_agent_generator_by_agent_generator_id(
            agent_generator_id=agent_generator_id,
        )
    except AgentGeneratorNotFoundServiceError:
        raise AgentGeneratorNotFoundAPIError.from_service_exception(
            service_exception=AgentGeneratorNotFoundServiceError(
                agent_generator_id="string",
            ),
        )
    except AgentGeneratorAlreadyRunningServiceError as exc:
        raise AgentGeneratorAlreadyRunningAPIError.from_service_exception(
            service_exception=exc,
        )

    return SuccessResponseModel()
