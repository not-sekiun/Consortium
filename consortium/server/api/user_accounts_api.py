from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    user_accounts_api_exceptions as api_excs,
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
    user_accounts_service_exceptions as svc_excs,
)
from consortium.server.models.request_body_models import (
    CreateUserAccountRequestBodyModel,
)
from consortium.server.models.request_data_models import (
    UpdateOwnUserAccountRequestDataModel,
    UpdateUserAccountByUserAccountIDRequestDataModel,
)
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

router = APIRouter(
    prefix="/api/user-accounts",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["User Accounts"],
)

_user_accounts_service = server_singletons.user_accounts_service
_users_service = server_singletons.users_service

_user_account_not_found_error = api_excs.UserAccountNotFoundError(
    user_account_id="<user_account_id>",
)
_user_account_authentication_error = api_excs.UserAccountAuthenticationError()
_user_account_username_already_exists_error_during_creation = api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
    consortium_exception=svc_excs.UserAccountUsernameAlreadyExistsError._during_user_account_creation(
        username="<username>",
    ),
)
_empty_user_account_username_error_during_creation = api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
    consortium_exception=svc_excs.EmptyUserAccountUsernameError()._during_user_account_creation(),
)
_empty_user_account_password_error_during_creation = api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
    consortium_exception=svc_excs.EmptyUserAccountPasswordError()._during_user_account_creation(),
)
_invalid_user_account_role_error_during_creation = api_excs.InvalidUserAccountRoleError.from_consortium_exception(
    consortium_exception=svc_excs.InvalidUserAccountRoleError._during_user_account_creation(
        role="<role>",
    ),
)
_user_account_username_already_exists_error_during_modification = api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
    consortium_exception=svc_excs.UserAccountUsernameAlreadyExistsError._during_user_account_modification(
        username="<username>",
        user_account_str="<user_account>",
    ),
)
_empty_user_account_username_error_during_modification = api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
    consortium_exception=svc_excs.EmptyUserAccountUsernameError()._during_user_account_modification(
        user_account_str="<user_account>"
    ),
)
_empty_user_account_password_error_during_modification = api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
    consortium_exception=svc_excs.EmptyUserAccountPasswordError()._during_user_account_modification(
        user_account_str="<user_account>"
    ),
)
_invalid_user_account_role_error_during_modification = api_excs.InvalidUserAccountRoleError.from_consortium_exception(
    consortium_exception=svc_excs.InvalidUserAccountRoleError._during_user_account_modification(
        user_account_str="<user_account>", role="<role>"
    ),
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
)
_invalid_uuid_error = InvalidUUIDError(
    resource_name="user account", uuid_value="<uuid_value>"
)


@router.get(
    "/all",
    responses={
        200: {"model": list[UserAccountModel]},
    },
)
async def get_all_user_accounts(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_USER_ACCOUNTS)),
    ],
) -> list[UserAccountModel]:
    return _user_accounts_service.get_all_user_accounts()


@router.get(
    "/me",
    responses={
        200: {"model": UserAccountModel},
    },
)
async def get_own_user_account(
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_OWN_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    return user.user_account


@router.get(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": _user_account_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model(),
        },
    },
)
async def get_user_account_by_user_account_id(
    user_account_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_USER_ACCOUNT_BY_USER_ACCOUNT_ID),
        ),
    ],
) -> UserAccountModel:
    try:
        return _user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=str(user_account_id),
        )
    except svc_excs.UserAccountIDNotFoundError:
        raise api_excs.UserAccountNotFoundError(
            user_account_id=str(user_account_id),
        ) from None


@router.post(
    "",
    status_code=201,
    responses={
        201: {"model": UserAccountModel},
        409: {
            "model": _user_account_username_already_exists_error_during_creation.to_pydantic_model()
        },
        422: {
            "model": _empty_user_account_username_error_during_creation.to_pydantic_model()
            | _empty_user_account_password_error_during_creation.to_pydantic_model()
            | _invalid_user_account_role_error_during_creation.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def create_user_account(
    create_user_account_request_body: CreateUserAccountRequestBodyModel,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    username = create_user_account_request_body.username
    password = create_user_account_request_body.password
    role = create_user_account_request_body.role

    try:
        new_user_account = _user_accounts_service.create_user_account(
            username=username,
            password=password,
            role=role,
        )
    except svc_excs.EmptyUserAccountUsernameError as exc:
        raise api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.EmptyUserAccountPasswordError as exc:
        raise api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.InvalidUserAccountRoleError as exc:
        raise api_excs.InvalidUserAccountRoleError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.UserAccountUsernameAlreadyExistsError as exc:
        raise api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    try:
        _user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerError() from None

    return new_user_account


@router.patch(
    "/me",
    responses={
        200: {"model": UserAccountModel},
        403: {"model": _user_account_authentication_error.to_pydantic_model()},
        404: {
            "model": _user_account_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _user_account_username_already_exists_error_during_modification.to_pydantic_model()
            | _empty_user_account_username_error_during_modification.to_pydantic_model()
            | _empty_user_account_password_error_during_modification.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def update_own_user_account(
    request_data: UpdateOwnUserAccountRequestDataModel,
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.UPDATE_OWN_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    # It is possible for the user account to not be found if it was deleted while the
    # user was logged in.
    user_account_id = str(user.user_account.user_account_id)
    try:
        user_account = _user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except svc_excs.UserAccountIDNotFoundError:
        raise api_excs.UserAccountNotFoundError(
            user_account_id=user_account_id
        ) from None
    if request_data.password is not None:
        if request_data.password.old_password != user_account.password:
            raise api_excs.UserAccountAuthenticationError()

    try:
        updated_user_account = (
            _user_accounts_service.update_user_account_by_user_account_id(
                user_account_id=user_account_id,
                username=request_data.username,
                password=request_data.password.new_password
                if request_data.password is not None
                else None,
            )
        )
    except svc_excs.UserAccountUsernameAlreadyExistsError as exc:
        raise api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.EmptyUserAccountUsernameError as exc:
        raise api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.EmptyUserAccountPasswordError as exc:
        raise api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    # Write the updated user accounts data to disk.
    try:
        _user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerError() from None

    return updated_user_account


@router.patch(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": _user_account_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _user_account_username_already_exists_error_during_modification.to_pydantic_model()
            | _empty_user_account_username_error_during_modification.to_pydantic_model()
            | _empty_user_account_password_error_during_modification.to_pydantic_model()
            | _invalid_user_account_role_error_during_modification.to_pydantic_model()
            | _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def update_user_account_by_user_account_id(
    user_account_id: UUID4,
    request_data: UpdateUserAccountByUserAccountIDRequestDataModel,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> UserAccountModel:
    try:
        updated_user_account = (
            _user_accounts_service.update_user_account_by_user_account_id(
                user_account_id=str(user_account_id),
                username=request_data.username,
                password=request_data.password,
                role=request_data.role,
            )
        )
    except svc_excs.UserAccountUsernameAlreadyExistsError as exc:
        raise api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.EmptyUserAccountUsernameError as exc:
        raise api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.EmptyUserAccountPasswordError as exc:
        raise api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.InvalidUserAccountRoleError as exc:
        raise api_excs.InvalidUserAccountRoleError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    except svc_excs.UserAccountNotFoundError:
        raise api_excs.UserAccountNotFoundError(
            user_account_id=str(user_account_id),
        ) from None

    # Write the updated user accounts data to disk.
    try:
        _user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerError() from None

    return updated_user_account


@router.delete(
    "/{user_account_id}",
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _user_account_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def delete_user_account_by_user_account_id(
    user_account_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.DELETE_USER_ACCOUNT_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> None:
    try:
        _user_accounts_service.delete_user_account_by_user_account_id(
            user_account_id=str(user_account_id),
        )
    except svc_excs.UserAccountIDNotFoundError:
        raise api_excs.UserAccountNotFoundError(
            user_account_id=str(user_account_id),
        ) from None

    # Write the updated user accounts data to disk.
    try:
        _user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerError() from None
