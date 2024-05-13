import copy
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.listeners_api_exceptions import (
    InvalidListenerParameterNameError,
    InvalidListenerParameterValueError,
    ListenerAlreadyRunningError,
    ListenerCancellationError,
    ListenerNotFoundError,
    ListenerNotRunningError,
    ListenerStartError,
    ListenerStopError,
    ListenerTemplateResolutionError,
)

# Framework exceptions are raised by the user of the framework themselves to
# distinguish them from the internally raised and handled server exceptions.
from consortium.server.framework.exceptions import (
    ListenerCancellationError as FrameworkListenerCancellationError,
)
from consortium.server.framework.exceptions import (
    ListenerStartError as FrameworkListenerStartError,
)
from consortium.server.framework.exceptions import (
    ListenerStopError as FrameworkListenerStopError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.listener_models import ListenerModel
from consortium.server.models.request_body_models import (
    NewListenerAttributesRequestBodyModel,
)
from consortium.server.objects.example_objects import example_listener_type
from consortium.server.objects.listener_objects import ListenerState
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/listeners",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Listeners API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
listeners_service = server_singletons.listeners_service
listener_templates_service = server_singletons.listener_templates_service


@router.get(
    "/all",
    responses={
        200: {"model": list[ListenerModel]},
    },
)
def get_all_listeners(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_LISTENERS)),
    ],
):
    return [
        ListenerModel(**listener.to_json())
        for listener in listeners_service.get_all_listeners()
    ]


@router.get(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def get_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_LISTENER_BY_LISTENER_ID),
        ),
    ],
):
    try:
        return ListenerModel(
            **listeners_service.get_listener_by_listener_id(listener_id).to_json(),
        )
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)


@router.post(
    "/{listener_id}/start",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStartError().to_pydantic_model()},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        409: {"model": ListenerAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def start_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.START_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)

    if listener.status.state == ListenerState.RUNNING:
        raise ListenerAlreadyRunningError(
            message="The listener cannot be started because it is already running",
        )

    try:
        await listener.start_listener()
    except FrameworkListenerStartError as exc:
        raise ListenerStartError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.post(
    "/{listener_id}/stop",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerStopError(message="string").to_pydantic_model()},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        409: {"model": ListenerNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def stop_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.STOP_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    if listener.status.state != ListenerState.RUNNING:
        raise ListenerNotRunningError(
            message="The listener cannot be stopped because it is not running.",
        )

    try:
        await listener.stop_listener()
    except FrameworkListenerStopError as exc:
        raise ListenerStopError(message=exc.message, detail=exc.detail)

    return SuccessResponseModel()


@router.post(
    "/{listener_id}/cancel",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": ListenerCancellationError(message="string").to_pydantic_model()},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        409: {"model": ListenerNotRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def cancel_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CANCEL_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)

    if listener.status.state != ListenerState.RUNNING:
        raise ListenerNotRunningError(
            message="The listener cannot be cancelled because it is not running.",
        )

    try:
        await listener.cancel_listener()
    except FrameworkListenerCancellationError as exc:
        raise ListenerCancellationError(message=exc.message, detail=exc.detail)
    except Exception as exc:
        raise InternalServerError(
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    return SuccessResponseModel()


@router.patch(
    "/{listener_id}",
    responses={
        200: {"model": ListenerModel},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        409: {"model": ListenerAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model()
            | InvalidListenerParameterNameError(
                parameter_name="string",
            ).to_pydantic_model()
            | InvalidListenerParameterValueError(
                parameter_name="string",
                parameter_value="string",
                exception=Exception("string"),
            ).to_pydantic_model(),
        },
        500: {
            "model": ListenerTemplateResolutionError(
                listener_type=example_listener_type,
            ).to_pydantic_model(),
        },
    },
)
def update_listener_by_listener_id(
    listener_id: str,
    # The only update-able listener attributes are its name, description and parameters
    # within the listener. Note that when instantiating the listener through its
    # listener template the options of a listener template are responsible for setting
    # both the name and endpoint string of the listener. Hence, when updating the
    # parameters of a listener, the name and endpoint strings are also updated by
    # running those update values through the listener template. However, it is
    # possible to update the name of a listener independently of the parameters by
    # simply not specifying any parameters when PUTing. But if the parameters are
    # present they will override the name string even if it was specified in the
    # request.
    updated_listener_attributes: NewListenerAttributesRequestBodyModel,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.UPDATE_LISTENER_BY_LISTENER_ID)),
    ],
) -> ListenerModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)
    new_name = updated_listener_attributes.name
    new_description = updated_listener_attributes.description
    new_parameters = updated_listener_attributes.parameters

    if new_description is not None:
        listener.description = new_description
    if new_parameters is not None:
        if listener.status.state == ListenerState.RUNNING:
            raise ListenerAlreadyRunningError(
                "The listener is already running. Stop it before attempting to update "
                "its parameters",
            )

        # It should be impossible for this for loop to break out without finding
        # the listener template that matches the target listener or to trip up on a
        # false positive based on listener type because all listener types are
        # unique to their respective listener
        found_listener_template = False
        for (
            test_listener_template
        ) in listener_templates_service.get_all_listener_templates():
            if test_listener_template.listener_type == listener.listener_type:
                found_listener_template = True
                listener_template = test_listener_template
                break
        # This should never be raised unless a programmer error is made.
        if not found_listener_template:
            raise ListenerTemplateResolutionError(
                listener_type=listener.listener_type,
            )

        for parameter_name, parameter_value in listener.parameters.items():
            if parameter_name not in new_parameters:
                # parameter_value could be a list or a dict, so we need to perform
                # a deep copy to prevent reference sharing.
                new_parameters[parameter_name] = copy.deepcopy(parameter_value)

        for parameter_name, parameter_value in new_parameters.items():
            if parameter_name not in listener_template.options:
                raise InvalidListenerParameterNameError(
                    parameter_name=parameter_name,
                )
            new_parameters[parameter_name] = parameter_value

        # At this point new_parameters contains all the parameters that a listener
        # would have. Any parameters not specified in the request body as part of
        # the JSON under the key "parameters" will be the same as the previous
        # listener.
        for parameter_name, parameter_value in new_parameters.items():
            try:
                listener_template.options[parameter_name].set_option_value(
                    parameter_value,
                )
            except ValueError as exc:
                raise InvalidListenerParameterValueError(
                    parameter_name=parameter_name,
                    parameter_value=parameter_value,
                    exception=exc,
                )

        # Create a temporary listener whose attributes we copy over to the
        # existing listener. This allows us to perform the name and
        # endpoint resolution required to update the attribute without
        # inadvertently overwriting any existing state within the existing
        # listener
        temporary_listener = listener_template.create_listener()
        listener.name = temporary_listener.name
        listener.endpoint = temporary_listener.endpoint
        listener.parameters = copy.deepcopy(temporary_listener.parameters)
    # Update name after options to overwrite the name if it is set in options.
    if new_name is not None:
        listener.name = new_name

    return ListenerModel(**listener.to_json())


@router.delete(
    "/{listener_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": ListenerNotFoundError(listener_id="string").to_pydantic_model()},
        409: {"model": ListenerAlreadyRunningError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
def delete_listener_by_listener_id(
    listener_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_LISTENER_BY_LISTENER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        listener = listeners_service.get_listener_by_listener_id(listener_id)
    except ValueError:
        raise ListenerNotFoundError(listener_id=listener_id)

    if listener.status.state == ListenerState.RUNNING:
        raise ListenerAlreadyRunningError(
            "The listener is already running. Stop it before attempting to delete "
            "it",
        )
    listeners_service.remove_listener(listener)
    return SuccessResponseModel()
