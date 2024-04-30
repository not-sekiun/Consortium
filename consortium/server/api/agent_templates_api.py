from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.agent_templates_api_exceptions import (
    AgentTemplateNotFoundError,
    InvalidAgentTemplateOptionNameError,
    InvalidAgentTemplateOptionValueError,
)
from consortium.server.exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agent-templates",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agent_templates_service = server_singletons.agent_templates_service
agent_generators_service = server_singletons.agent_generators_service


@router.post(
    "/{agent_template_id}",
    responses={
        201: {"model": AgentGeneratorModel},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidAgentTemplateOptionValueError(
                option_name="string",
                option_value="string",
                exception=Exception("string"),
            ).to_pydantic_model()
            | InvalidAgentTemplateOptionNameError(
                option_name="string",
            ).to_pydantic_model(),
        },
        404: {
            "model": AgentTemplateNotFoundError(
                agent_template_id="string",
            ).to_pydantic_model(),
        },
    },
    status_code=201,
)
def create_agent_generator_through_agent_template_by_agent_template_id(
    agent_template_id: str,
    agent_template_options: dict[str, Any],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_AGENT_GENERATOR)),
    ],
) -> AgentGeneratorModel:
    try:
        agent_template = (
            agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
            )
        )
    except ValueError:
        raise AgentTemplateNotFoundError(agent_template_id=agent_template_id)

    for option_name, option_value in agent_template_options.items():
        try:
            agent_template.set_option_value(option_name, option_value)
        # KeyError is raised when option_name is invalid.
        except KeyError:
            raise InvalidAgentTemplateOptionNameError(option_name=option_name)
        # ValueError is raised when option_value is invalid.
        except ValueError as exc:
            raise InvalidAgentTemplateOptionValueError(
                option_name=option_name,
                option_value=option_value,
                exception=exc,
            )

    # Agent generator is created and added to the agent generator service but not
    # explicitly started. Starting the agent generator must be manually done from the
    # /api/agent-generators endpoint.
    agent_generator = agent_template.create_agent_generator()
    agent_template.clear_all_option_values()
    agent_generators_service.add_agent_generator(agent_generator)

    return AgentGeneratorModel(**agent_generator.to_json())


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentTemplateModel]},
    },
)
def get_all_agent_templates(
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_TEMPLATES),
        ),
    ],
) -> list[AgentTemplateModel]:
    return [
        AgentTemplateModel(**agent_template.to_json())
        for agent_template in agent_templates_service.get_all_agent_templates()
    ]


@router.get(
    "/{agent_template_id}",
    responses={
        200: {"model": AgentTemplateModel},
        404: {
            "model": AgentTemplateNotFoundError(
                agent_template_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def get_agent_template_by_agent_template_id(
    agent_template_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.READ_AGENT_TEMPLATE_BY_AGENT_TEMPLATE_ID,
            ),
        ),
    ],
) -> AgentTemplateModel:
    try:
        agent_template = (
            agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id,
            )
        )
    except ValueError:
        raise AgentTemplateNotFoundError(agent_template_id=agent_template_id)

    return AgentTemplateModel(**agent_template.to_json())
