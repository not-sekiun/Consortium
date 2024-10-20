from typing import Annotated, Any

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.listener_templates_api_exceptions import (
    EmptyListenerNameError as EmptyListenerNameAPIError,
    ListenerTemplateNotFoundError as ListenerTemplateNotFoundAPIError,
    ListenerTemplateOptionNotFoundError as ListenerTemplateOptionNotFoundAPIError,
    ListenerTemplateOptionValueError as ListenerTemplateOptionValueAPIError,
)
from consortium.server.exceptions.framework_exceptions.listener_template_framework_exceptions import (
    ListenerTemplateOptionNotFoundError as ListenerTemplateOptionNotFoundFrameworkError,
    ListenerTemplateOptionValueError as ListenerTemplateOptionValueFrameworkError,
)
from consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions import (
    ListenerTemplateNotFoundError as ListenerTemplateNotFoundServiceError,
)
from consortium.server.exceptions.service_exceptions.listeners_service_exceptions import (
    EmptyListenerNameError as EmptyListenerNameServiceError,
    ListenerTemplateOptionNotFoundError as ListenerTemplateOptionNotFoundServiceError,
    ListenerTemplateOptionValueError as ListenerTemplateOptionValueServiceError,
)
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.listener_template_models import ListenerTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

_example_listener_template_option_value_framework_error = (
    ListenerTemplateOptionValueFrameworkError(
        listener_template="string",
        option_name="string",
        option_value="string",
        error_message="string",
    )
)
_example_listener_template_option_not_found_framework_error = (
    ListenerTemplateOptionNotFoundFrameworkError(
        option_name="string",
        listener_template="string",
    )
)
listener_templates_service = server_singletons.listener_templates_service
listeners_service = server_singletons.listeners_service
router = APIRouter(
    prefix="/api/listener-templates",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Listener Templates API"],
)


@router.post(
    "/{listener_template_id}",
    responses={
        201: {"model": ListenerModel},
        404: {
            "model": ListenerTemplateNotFoundAPIError.from_service_exception(
                service_exception=ListenerTemplateNotFoundServiceError(
                    listener_template_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | ListenerTemplateOptionValueAPIError.from_service_exception(
                service_exception=ListenerTemplateOptionValueServiceError(
                    message=_example_listener_template_option_value_framework_error.message,
                    detail=_example_listener_template_option_value_framework_error.detail,
                ),
            ).to_pydantic_model()
            | ListenerTemplateOptionNotFoundAPIError.from_service_exception(
                service_exception=ListenerTemplateOptionNotFoundServiceError(
                    message=_example_listener_template_option_not_found_framework_error.message,
                    detail=_example_listener_template_option_not_found_framework_error.detail,
                ),
            ).to_pydantic_model()
            | EmptyListenerNameAPIError.from_service_exception(
                service_exception=EmptyListenerNameServiceError(),
            ).to_pydantic_model(),
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
        listener = await listeners_service.create_listener_from_listener_template_by_listener_template_id(
            listener_template_id=listener_template_id,
            options=options,
        )
    except ListenerTemplateNotFoundServiceError as exc:
        raise ListenerTemplateNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except ListenerTemplateOptionNotFoundServiceError as exc:
        raise ListenerTemplateOptionNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except ListenerTemplateOptionValueServiceError as exc:
        raise ListenerTemplateOptionValueAPIError.from_service_exception(
            service_exception=exc,
        )
    except EmptyListenerNameServiceError as exc:
        raise EmptyListenerNameAPIError.from_service_exception(
            service_exception=exc,
        )

    return ListenerModel(**listener.to_json())


@router.get(
    "/all",
    responses={200: {"model": list[ListenerTemplateModel]}},
)
def get_all_listener_templates_info(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_LISTENER_TEMPLATES)),
    ],
):
    return [
        ListenerTemplateModel(**listener_template.to_json())
        for listener_template in listener_templates_service.get_all_listener_templates()
    ]


@router.get(
    "/{listener_template_id}",
    responses={
        200: {"model": ListenerTemplateModel},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
        404: {
            "model": ListenerTemplateNotFoundAPIError.from_service_exception(
                service_exception=ListenerTemplateNotFoundServiceError(
                    listener_template_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
)
def get_listener_template_info_by_listener_templates_id(
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
            listener_templates_service.get_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
            )
        )
    except ListenerTemplateNotFoundServiceError as exc:
        raise ListenerTemplateNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )

    return ListenerTemplateModel(**listener_template.to_json())
