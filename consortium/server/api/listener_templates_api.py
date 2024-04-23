from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.listener_template_models import ListenerTemplateModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.server_exceptions import (
    InternalServerError,
    InvalidListenerTemplateOptionNameError,
    InvalidListenerTemplateOptionValueError,
    ListenerTemplateNotFoundError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)

router = APIRouter(
    prefix="/api/listener-templates",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
listener_templates_service = server_singletons.listener_templates_service
listeners_service = server_singletons.listeners_service


@router.post(
    "/{listener_template_id}",
    responses={
        201: {"model": ListenerModel},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidListenerTemplateOptionValueError(
                detail="string",
            ).to_pydantic_model()
            | InvalidListenerTemplateOptionNameError().to_pydantic_model(),
        },
        404: {"model": ListenerTemplateNotFoundError().to_pydantic_model()},
    },
    status_code=201,
)
def create_listener_through_listener_template_by_listener_template_id(
    listener_template_id: str,
    listener_template_options: Dict[str, Any],
    _: Annotated[None, Depends(AuthorizeUserRequest(UserPermissions.CREATE_LISTENER))],
) -> ListenerModel:
    try:
        listener_template = (
            listener_templates_service.get_listener_template_by_listener_template_id(
                listener_template_id,
            )
        )
    except ValueError:
        raise ListenerTemplateNotFoundError

    for option_name, option_value in listener_template_options.items():
        try:
            listener_template.set_option_value(option_name, option_value)
        # KeyError is raised when the option_name is invalid
        except KeyError:
            raise InvalidListenerTemplateOptionNameError
        # ValueError is raised when the option_value is invalid
        except ValueError as exc:
            raise InvalidListenerTemplateOptionValueError(detail=str(exc))

    # Listener is created and added to the listeners service but not explicitly
    # started. Starting the listener must be manually done from the /api/listeners
    # endpoint.
    listener = listener_template.create_listener()
    listener_template.clear_all_options_values()
    listeners_service.add_listener(listener)

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
    print(listener_templates_service.get_all_listener_templates()[0].to_json())
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
        404: {"model": ListenerTemplateNotFoundError().to_pydantic_model()},
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
    except ValueError:
        raise ListenerTemplateNotFoundError

    return ListenerTemplateModel(**listener_template.to_json())
