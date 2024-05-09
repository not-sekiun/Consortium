import copy
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
    AgentTemplateResolutionError,
    InvalidAgentGeneratorParameterNameError,
    InvalidAgentGeneratorParameterValueError,
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
from consortium.server.models.request_body_models import (
    NewAgentGeneratorAttributesRequestBodyModel,
)
from consortium.server.objects.agent_generator_objects import AgentGeneratorState
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
                UserPermissions.STOP_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
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


@router.patch(
    "/{agent_generator_id}",
    responses={
        200: {"model": AgentGeneratorModel},
        404: {
            "model": AgentGeneratorNotFoundError(
                agent_generator_id="string",
            ).to_pydantic_model(),
        },
        409: {"model": AgentGeneratorAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidAgentGeneratorParameterNameError(
                parameter_name="string",
            ).to_pydantic_model()
            | InvalidAgentGeneratorParameterValueError(
                parameter_name="string",
                parameter_value="string",
                exception=Exception("string"),
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
    # The only update-able agent generator attributes are its name, description and
    # parameters within the agent generator. Note that when instantiating the agent
    # generator through its agent template the options of an agent template are
    # responsible for setting the name of the agent generator. Hence, when updating the
    # parameters of an agent generator, the name is also updated by running those update
    # values through the agent template. However, it is possible to update the name of
    # an agent generator independently of the parameters by simply not specifying any
    # parameters when PUTing. But if the parameters are present they will override the
    # name string even if it was specified in the request.
    updated_agent_generator_attributes: NewAgentGeneratorAttributesRequestBodyModel,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
    ],
) -> AgentGeneratorModel:
    try:
        agent_generator = (
            agent_generators_service.get_agent_generator_by_agent_generator_id(
                agent_generator_id,
            )
        )
    except ValueError:
        raise AgentGeneratorNotFoundError(agent_generator_id)
    new_name = updated_agent_generator_attributes.name
    new_description = updated_agent_generator_attributes.description
    new_parameters = updated_agent_generator_attributes.parameters

    if new_description is not None:
        agent_generator.description = new_description
    if new_parameters is not None:
        if agent_generator.status.state == AgentGeneratorState.RUNNING:
            raise AgentGeneratorAlreadyRunningError(
                "The agent generator is already running. Stop it before attempting to "
                "update its parameters",
            )

        # It should be impossible for this for loop to break out without finding
        # the agent template that matches the target agent generator or to trip up on a
        # false positive based on agent type because all agent types are
        # unique to their respective agent generators
        found_agent_template = False
        for test_agent_template in agent_templates_service.get_all_agent_templates():
            if test_agent_template.agent_type == agent_generator.agent_type:
                found_agent_template = True
                agent_template = test_agent_template
                break
        # This should never be raised unless a programmer error is made.
        if not found_agent_template:
            raise AgentTemplateResolutionError(
                agent_type=agent_generator.agent_type,
            )

        for parameter_name, parameter_value in agent_generator.parameters.items():
            if parameter_name not in new_parameters:
                # parameter_value could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                new_parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in new_parameters.items():
            if parameter_name not in agent_template.options:
                raise InvalidAgentGeneratorParameterNameError(
                    parameter_name=parameter_name,
                )
            new_parameters[parameter_name] = parameter_value

        # At this point new_parameters contains all the parameters that an agent
        # generator would have. Any parameters not specified in the request body as
        # part of the JSON under the key "parameters" will be the same as the previous
        # agent generator.
        for parameter_name, parameter_value in new_parameters.items():
            try:
                agent_template.options[parameter_name].set_option_value(
                    parameter_value,
                )
            except ValueError as exc:
                raise InvalidAgentGeneratorParameterValueError(
                    parameter_name=parameter_name,
                    parameter_value=parameter_value,
                    exception=exc,
                )

        # Create a temporary agent generator whose attributes we copy over to the
        # existing agent generator. This allows us to perform the name resolution
        # required to update the attribute without inadvertently overwriting any
        # existing state within the existing agent generator.
        temporary_agent_generator = agent_template.create_agent_generator()
        agent_generator.name = temporary_agent_generator.name
        agent_generator.parameters = copy.deepcopy(temporary_agent_generator.parameters)
    # Update name after options to overwrite the name if it is set in options.
    if new_name is not None:
        agent_generator.name = new_name

    return AgentGeneratorModel(**agent_generator.to_json())


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
        Depends(
            AuthorizeUserRequest(
                UserPermissions.DELETE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            ),
        ),
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
