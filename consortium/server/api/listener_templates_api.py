from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions import (
    listener_templates_framework_exceptions,
)
from consortium.server.exceptions.api_exceptions import (
    listener_templates_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.service_exceptions import (
    listener_templates_service_exceptions as svc_excs,
)
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.listener_template_models import ListenerTemplateModel
from consortium.server.models.union_response_models import (
    ListenerTemplateOptionsValidationErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/listener-templates",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Listener Templates"],
)

_listener_templates_service = server_singletons.listener_templates_service
_listeners_service = server_singletons.listeners_service

_listener_template_not_found_error = (
    api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.ListenerTemplateIDNotFoundError(
            listener_template_id="<listener_template_id>"
        )
    )
)


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
        404: {"model": _listener_template_not_found_error.to_pydantic_model()},
        422: {"model": RequestValidationErrorResponse},
    },
)
def get_listener_template_by_listener_template_id(
    listener_template_id: UUID4,
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
    except svc_excs.ListenerTemplateNotFoundError as exc:
        raise api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return ListenerTemplateModel(**listener_template.to_json())


@router.post(
    "/{listener_template_id}",
    status_code=201,
    responses={
        201: {"model": ListenerModel},
        404: {"model": _listener_template_not_found_error.to_pydantic_model()},
        422: {"model": ListenerTemplateOptionsValidationErrorResponse},
    },
)
async def create_listener_through_listener_template_by_listener_template_id(
    listener_template_id: UUID4,
    options: dict[str, Any],
    _: Annotated[None, Depends(AuthorizeUserRequest(UserPermissions.CREATE_LISTENER))],
) -> ListenerModel:
    try:
        listener = _listeners_service.create_listener_from_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
            parameters=options,
        )
    except svc_excs.ListenerTemplateNotFoundError as exc:
        raise api_excs.ListenerTemplateNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        listener_templates_framework_exceptions.ListenerTemplateOptionNotFoundError
    ) as exc:
        raise api_excs.ListenerTemplateOptionNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listener_templates_framework_exceptions.ListenerTemplateOptionValueValidationError as exc:
        raise api_excs.ListenerTemplateOptionValueValidationError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except listener_templates_framework_exceptions.MissingRequiredListenerTemplateOptionError as exc:
        raise api_excs.MissingRequiredListenerTemplateOptionError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except (
        listener_templates_framework_exceptions.ListenerTemplateValidatingFunctionError
    ) as exc:
        raise api_excs.ListenerTemplateValidatingFunctionError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    return ListenerModel(**listener.to_json())
