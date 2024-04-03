from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.agent_generator_template_models import (
    AgentGeneratorTemplateModel,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.server_exceptions import (
    AgentGeneratorTemplateNotFoundError,
    InvalidAgentGeneratorTemplateOptionNameError,
    InvalidAgentGeneratorTemplateOptionValueError,
    UnprocessableEntityError,
)

router = APIRouter(
    prefix="/api/agent-generator-templates",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
agent_generator_templates_service = server_singletons.agent_generator_templates_service
agent_generators_service = server_singletons.agent_generators_service


@router.post(
    "/{agent_generator_template_id}",
    responses={
        201: {"model": AgentGeneratorModel},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidAgentGeneratorTemplateOptionValueError(
                detail="string",
            ).to_pydantic_model()
            | InvalidAgentGeneratorTemplateOptionNameError().to_pydantic_model(),
        },
        404: {"model": AgentGeneratorTemplateNotFoundError().to_pydantic_model()},
    },
    status_code=201,
)
def create_agent_generator_through_agent_generator_template_by_agent_generator_template_id(
    agent_generator_template_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_AGENT_GENERATOR)),
    ],
) -> AgentGeneratorModel:
    try:
        agent_generator_template = agent_generator_templates_service.create_agent_generator_through_agent_generator_template_by_agent_generator_template_id(
            agent_generator_template_id,
        )
    except ValueError:
        raise AgentGeneratorTemplateNotFoundError

    for option_name, option_value in agent_generator_template.options.items():
        try:
            agent_generator_template.set_option_value(option_name, option_value)
        # KeyError is raised when option_name is invalid.
        except KeyError:
            raise InvalidAgentGeneratorTemplateOptionNameError
        # ValueError is raised when option_value is invalid.
        except ValueError as exc:
            raise InvalidAgentGeneratorTemplateOptionValueError(detail=str(exc))

    # Agent generator is created and added to the agent generator service but not
    # explicitly started. Starting the agent generator must be manually done from the
    # /api/agent-generators endpoint.
    agent_generator = agent_generator_template.create_agent_generator()
    agent_generator_template.clear_all_option_values()
    agent_generators_service.add_agent_generator(agent_generator)

    return AgentGeneratorModel(**agent_generator.to_json())


@router.get(
    "/all",
    responses={
        200: {"model": list[AgentGeneratorTemplateModel]},
    },
)
def get_all_agent_generator_templates(
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_ALL_AGENT_GENERATOR_TEMPLATES),
        ),
    ],
) -> list[AgentGeneratorTemplateModel]:
    return [
        AgentGeneratorTemplateModel(**agent_generator_template.to_json())
        for agent_generator_template in agent_generator_templates_service.get_all_agent_generator_templates()
    ]


@router.get(
    "/{agent_generator_template_id}",
    responses={
        200: {"model": AgentGeneratorTemplateModel},
        404: {"model": AgentGeneratorTemplateNotFoundError().to_pydantic_model()},
    },
)
def get_agent_generator_template_by_agent_generator_template_id(
    agent_generator_template_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.READ_AGENT_GENERATOR_TEMPLATE_BY_AGENT_GENERATOR_TEMPLATE_ID,
            ),
        ),
    ],
) -> AgentGeneratorTemplateModel:
    try:
        agent_generator_template = agent_generator_templates_service.get_agent_generator_template_by_agent_generator_template_id(
            agent_generator_template_id,
        )
    except ValueError:
        raise AgentGeneratorTemplateNotFoundError

    return AgentGeneratorTemplateModel(**agent_generator_template.to_json())
