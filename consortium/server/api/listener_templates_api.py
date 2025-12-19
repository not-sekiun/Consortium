from typing import Annotated, Any

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    listener_templates_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.consortium_exceptions import (
    listener_templates_consortium_exceptions as consortium_excs,
)
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.listener_template_models import ListenerTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/listener-templates",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Listener Templates API"],
)

_listener_templates_service = server_singletons.listener_templates_service
_listeners_service = server_singletons.listeners_service


_listener_template_not_found_error = (
    api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.ListenerTemplateIDNotFoundError(
            listener_template_id="<listener_template_id>"
        )
    )
)
_listener_template_option_value_validation_error = (
    api_excs.ListenerTemplateOptionValueValidationError.from_consortium_exception(
        consortium_exception=consortium_excs.ListenerTemplateOptionValueValidationError(
            listener_template_str="<listener_template_str>",
            option_name="<option_str>",
            option_value="<option_value>",
            error_message="<error_message>",
        )
    )
)
_listener_template_option_not_found_error = (
    api_excs.ListenerTemplateOptionNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.ListenerTemplateOptionNotFoundError(
            listener_template_str="<listener_template>", option_name="<option_str>"
        )
    )
)
_missing_required_listener_template_option_error = (
    api_excs.MissingRequiredListenerTemplateOptionError.from_consortium_exception(
        consortium_exception=consortium_excs.MissingRequiredListenerTemplateOptionError(
            listener_template_str="<listener_template>", option_name="<option_str>"
        )
    )
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}]
)


@router.post(
    "/{listener_template_id}",
    responses={
        201: {"model": ListenerModel},
        404: {"model": _listener_template_not_found_error.to_pydantic_model()},
        422: {
            "model": _unprocessable_entity_error.to_pydantic_model()
            | _listener_template_option_value_validation_error.to_pydantic_model()
            | _listener_template_option_not_found_error.to_pydantic_model()
            | _missing_required_listener_template_option_error.to_pydantic_model()
        },
    },
    status_code=201,
)
async def create_listener_through_listener_template_by_listener_template_id(
    listener_template_id: str,
    options: dict[str, Any],
    _: Annotated[None, Depends(AuthorizeUserRequest(UserPermissions.CREATE_LISTENER))],
) -> ListenerModel:
    try:
        listener = await _listeners_service.create_listener_from_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
            parameters=options,
        )
    except consortium_excs.ListenerTemplateNotFoundError as exc:
        raise api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.ListenerTemplateOptionNotFoundError as exc:
        raise api_excs.ListenerTemplateOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.ListenerTemplateOptionValueValidationError as exc:
        raise api_excs.ListenerTemplateOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except consortium_excs.MissingRequiredListenerTemplateOptionError as exc:
        raise api_excs.MissingRequiredListenerTemplateOptionError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return ListenerModel(**listener.to_json())


@router.get(
    "/all",
    responses={200: {"model": list[ListenerTemplateModel]}},
)
def get_all_listener_templates(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_LISTENER_TEMPLATES)),
    ],
):
    return [
        ListenerTemplateModel(**listener_template.to_json())
        for listener_template in _listener_templates_service.get_all_listener_templates()
    ]


@router.get(
    "/{listener_template_id}",
    responses={
        200: {"model": ListenerTemplateModel},
        422: {"model": _unprocessable_entity_error.to_pydantic_model()},
        404: {"model": _listener_template_not_found_error.to_pydantic_model()},
    },
)
def get_listener_template_by_listener_template_id(
    listener_template_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.READ_LISTENER_TEMPLATE_BY_LISTENER_TEMPLATE_ID,
            ),
        ),
    ],
):
    try:
        listener_template = (
            _listener_templates_service.get_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
            )
        )
    except consortium_excs.ListenerTemplateNotFoundError as exc:
        raise api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return ListenerTemplateModel(**listener_template.to_json())
