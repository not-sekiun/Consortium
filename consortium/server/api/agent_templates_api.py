from typing import Annotated, Any

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.agent_templates_api_exceptions import (
    AgentTemplateNotFoundError as AgentTemplateNotFoundAPIError,
    AgentTemplateOptionNotFoundError as AgentTemplateOptionNotFoundAPIError,
    AgentTemplateOptionValueError as AgentTemplateOptionValueAPIError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateOptionNotFoundError as AgentTemplateOptionNotFoundFrameworkError,
    AgentTemplateOptionValueError as AgentTemplateOptionValueFrameworkError,
)
from consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions import (
    AgentTemplateOptionNotFoundError as AgentTemplateOptionNotFoundServiceError,
    AgentTemplateOptionValueError as AgentTemplateOptionValueServiceError,
)
from consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions import (
    AgentTemplateNotFoundError as AgentTemplateNotFoundServiceError,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

_example_agent_template_option_value_framework_error = (
    AgentTemplateOptionValueFrameworkError(
        agent_template_str="string",
        option_name="string",
        option_value="string",
        error_message="string",
    )
)
_example_agent_template_option_not_found_framework_error = (
    AgentTemplateOptionNotFoundFrameworkError(
        agent_template_str="string",
        option_name="string",
    )
)
agent_templates_service = server_singletons.agent_templates_service
agent_generators_service = server_singletons.agent_generators_service
router = APIRouter(
    prefix="/api/agent-templates",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agent Templates API"],
)


@router.post(
    "/{agent_template_id}",
    responses={
        201: {"model": AgentGeneratorModel},
        404: {
            "model": AgentTemplateNotFoundAPIError.from_consortium_exception(
                consortium_exception=AgentTemplateNotFoundServiceError(
                    agent_template_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | AgentTemplateOptionValueAPIError.from_consortium_exception(
                consortium_exception=AgentTemplateOptionNotFoundServiceError(
                    message=_example_agent_template_option_value_framework_error.message,
                    detail=_example_agent_template_option_value_framework_error.detail,
                ),
            ).to_pydantic_model()
            | AgentTemplateOptionNotFoundAPIError.from_consortium_exception(
                consortium_exception=AgentTemplateOptionNotFoundServiceError(
                    message=_example_agent_template_option_not_found_framework_error.message,
                    detail=_example_agent_template_option_not_found_framework_error.detail,
                ),
            ).to_pydantic_model(),
        },
    },
    status_code=201,
)
async def create_agent_generator_through_agent_template_by_agent_template_id(
    agent_template_id: str,
    options: dict[str, Any],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_AGENT_GENERATOR)),
    ],
) -> AgentGeneratorModel:
    try:
        agent_generator = await agent_generators_service.create_agent_generator_from_agent_template_by_agent_template_id(
            agent_template_id=agent_template_id,
            parameters=options,
        )
    except AgentTemplateNotFoundServiceError as exc:
        raise AgentTemplateNotFoundAPIError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except AgentTemplateOptionNotFoundServiceError as exc:
        raise AgentTemplateOptionNotFoundAPIError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except AgentTemplateOptionValueServiceError as exc:
        raise AgentTemplateOptionValueAPIError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

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
            "model": AgentTemplateNotFoundAPIError.from_consortium_exception(
                consortium_exception=AgentTemplateNotFoundServiceError(
                    agent_template_id="string",
                ),
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
    except AgentTemplateNotFoundServiceError as exc:
        raise AgentTemplateNotFoundAPIError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return AgentTemplateModel(**agent_template.to_json())
