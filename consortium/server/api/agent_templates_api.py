from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions import (
    agent_templates_framework_exceptions,
)
from consortium.server.exceptions.api_exceptions import (
    agent_templates_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.service_exceptions import (
    agent_templates_service_exceptions as svc_excs,
)
from consortium.server.models.agent_generator_models import AgentGeneratorModel
from consortium.server.models.agent_template_models import AgentTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/agent-templates",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Agent Templates"],
)

_agent_templates_service = server_singletons.agent_templates_service
_agent_generators_service = server_singletons.agent_generators_service

_agent_template_not_found_error = (
    api_excs.AgentTemplateNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.AgentTemplateIDNotFoundError(
            agent_template_id="<agent_template_id>"
        )
    )
)
_agent_template_option_value_error = api_excs.AgentTemplateOptionValueValidationError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.AgentTemplateOptionValueValidationError(
        agent_template_str="<agent_template>",
        option_name="<option_str>",
        option_value="<option_value>",
        error_message="<error_message>",
    )
)
_agent_template_option_not_found_error = api_excs.AgentTemplateOptionNotFoundError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.AgentTemplateOptionNotFoundError(
        agent_template_str="<agent_template>", option_name="<option_str>"
    )
)
_missing_required_agent_template_option_error = api_excs.MissingRequiredAgentTemplateOptionError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.MissingRequiredAgentTemplateOptionError(
        agent_template_str="<agent_template>", option_name="<option_str>"
    )
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}]
)
_invalid_uuid_error = InvalidUUIDError(
    resource_name="agent template", uuid_value="<uuid_value>"
)


@router.post(
    "/{agent_template_id}",
    status_code=201,
    responses={
        201: {"model": AgentGeneratorModel},
        404: {"model": _agent_template_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _agent_template_option_value_error.to_pydantic_model()
            | _agent_template_option_not_found_error.to_pydantic_model()
            | _missing_required_agent_template_option_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
async def create_agent_generator_through_agent_template_by_agent_template_id(
    agent_template_id: UUID4,
    options: dict[str, Any],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_AGENT_GENERATOR)),
    ],
) -> AgentGeneratorModel:
    try:
        agent_generator = _agent_generators_service.create_agent_generator_from_agent_template_by_agent_template_id(
            agent_template_id=agent_template_id,
            parameters=options,
        )
    except svc_excs.AgentTemplateNotFoundError as exc:
        raise api_excs.AgentTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except agent_templates_framework_exceptions.AgentTemplateOptionNotFoundError as exc:
        raise api_excs.AgentTemplateOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        agent_templates_framework_exceptions.AgentTemplateOptionValueValidationError
    ) as exc:
        raise api_excs.AgentTemplateOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        agent_templates_framework_exceptions.MissingRequiredAgentTemplateOptionError
    ) as exc:
        raise api_excs.MissingRequiredAgentTemplateOptionError.from_consortium_exception(
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
        for agent_template in _agent_templates_service.get_all_agent_templates()
    ]


@router.get(
    "/{agent_template_id}",
    responses={
        200: {"model": AgentTemplateModel},
        404: {"model": _agent_template_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
)
def get_agent_template_by_agent_template_id(
    agent_template_id: UUID4,
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
            _agent_templates_service.get_agent_template_by_agent_template_id(
                agent_template_id,
            )
        )
    except svc_excs.AgentTemplateNotFoundError as exc:
        raise api_excs.AgentTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return AgentTemplateModel(**agent_template.to_json())
