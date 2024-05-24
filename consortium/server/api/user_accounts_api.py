from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenHTTPError,
    InternalServerErrorHTTPError,
    MethodNotAllowedHTTPError,
    UnauthorizedHTTPError,
    UnprocessableEntityHTTPError,
)
from consortium.server.exceptions.api_exceptions.user_accounts_api_exceptions import (
    EmptyUserAccountPasswordAPIError,
    EmptyUserAccountUsernameAPIError,
    IdenticalUserAccountPasswordAPIError,
    IdenticalUserAccountRoleAPIError,
    IdenticalUserAccountUsernameAPIError,
    InvalidUserAccountCredentials,
    InvalidUserAccountRoleAPIError,
    UserAccountNotFoundAPIError,
    UserAccountUsernameAlreadyExistsAPIError,
)
from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    EmptyUserAccountPasswordServiceError,
    EmptyUserAccountUsernameServiceError,
    IdenticalUserAccountPasswordServiceError,
    IdenticalUserAccountRoleServiceError,
    IdenticalUserAccountUsernameServiceError,
    InvalidUserAccountIDServiceError,
    InvalidUserAccountRoleServiceError,
    UserAccountsFileServiceError,
    UserAccountUsernameAlreadyExistsServiceError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserPermissions, UserRole
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

router = APIRouter(
    prefix="/api/user-accounts",
    responses={
        401: {"model": UnauthorizedHTTPError().to_pydantic_model()},
        403: {"model": ForbiddenHTTPError().to_pydantic_model()},
        405: {"model": MethodNotAllowedHTTPError().to_pydantic_model()},
        500: {"model": InternalServerErrorHTTPError().to_pydantic_model()},
    },
    tags=["User Accounts API"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
user_accounts_service = server_singletons.user_accounts_service
users_service = server_singletons.users_service


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
    return user_accounts_service.get_all_user_accounts()


@router.get(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
    },
)
async def get_user_account_by_user_account_id(
    user_account_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.READ_USER_ACCOUNT_BY_USER_ACCOUNT_ID),
        ),
    ],
) -> UserAccountModel:
    try:
        return user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=user_account_id)


@router.post(
    "",
    responses={
        201: {"model": UserAccountModel},
        422: {
            "model": UserAccountUsernameAlreadyExistsAPIError(
                username="string",
            ).to_pydantic_model()
            | EmptyUserAccountUsernameAPIError().to_pydantic_model()
            | EmptyUserAccountPasswordAPIError().to_pydantic_model()
            | InvalidUserAccountRoleAPIError(role="string").to_pydantic_model(),
        },
    },
    status_code=201,
)
async def create_user_account(
    username: Annotated[str, Body()],
    password: Annotated[str, Body()],
    role: Annotated[UserRole, Body()],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    try:
        new_user_account = user_accounts_service.create_user_account(
            username=username,
            password=password,
            role=role,
        )
    except EmptyUserAccountUsernameServiceError:
        raise EmptyUserAccountUsernameAPIError
    except EmptyUserAccountPasswordServiceError:
        raise EmptyUserAccountPasswordAPIError
    except InvalidUserAccountRoleServiceError:
        raise InvalidUserAccountRoleAPIError(role=role)
    except UserAccountUsernameAlreadyExistsServiceError:
        raise UserAccountUsernameAlreadyExistsAPIError(username=username)
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()

    return new_user_account


@router.patch(
    "/me/username",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id=None,
            ).to_pydantic_model(),
        },
        422: {
            "model": IdenticalUserAccountUsernameAPIError(
                username="string",
            ).to_pydantic_model()
            | UserAccountUsernameAlreadyExistsAPIError(
                username="string",
            ).to_pydantic_model(),
        },
    },
)
def update_own_user_account_username(
    username: Annotated[str, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_OWN_USER_ACCOUNT_USERNAME,
            ),
        ),
    ],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=None)

    old_user_account_username = user_account.username
    try:
        user_account = (
            user_accounts_service.update_user_account_username_by_user_account_id(
                user_account_id=user_account.user_account_id,
                username=username,
            )
        )
    except UserAccountUsernameAlreadyExistsServiceError:
        raise UserAccountUsernameAlreadyExistsAPIError(username=username)
    except IdenticalUserAccountUsernameServiceError:
        raise IdenticalUserAccountUsernameAPIError(username=username)
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()
    for user in users_service.get_all_users():
        if user.username == old_user_account_username:
            user.username = user_account.username

    return user_account


@router.patch(
    "/{user_account_id}/username",
    responses={
        200: {"model": None},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": IdenticalUserAccountUsernameAPIError(
                username="string",
            ).to_pydantic_model()
            | UserAccountUsernameAlreadyExistsAPIError(
                username="string",
            ).to_pydantic_model(),
        },
    },
)
def update_user_account_username_by_user_account_id(
    user_account_id: str,
    username: Annotated[str, Body(embed=True)],
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_USERNAME_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> None:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=user_account_id)

    old_user_account_username = user_account.username
    try:
        user_account = (
            user_accounts_service.update_user_account_username_by_user_account_id(
                user_account_id=user_account.user_account_id,
                username=username,
            )
        )
    except UserAccountUsernameAlreadyExistsServiceError:
        raise UserAccountUsernameAlreadyExistsAPIError(username=username)
    except IdenticalUserAccountUsernameServiceError:
        raise IdenticalUserAccountUsernameAPIError(username=username)
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()
    for user in users_service.get_all_users():
        if user.username == old_user_account_username:
            user.username = username

    return user_account


@router.patch(
    "/me/password",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id=None,
            ).to_pydantic_model(),
        },
        422: {
            "model": EmptyUserAccountPasswordAPIError().to_pydantic_model()
            | IdenticalUserAccountPasswordAPIError().to_pydantic_model(),
        },
    },
)
def update_own_user_account_password(
    old_password: Annotated[str, Body()],
    new_password: Annotated[str, Body()],
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_OWN_USER_ACCOUNT_PASSWORD,
            ),
        ),
    ],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=None)
    if old_password != user_account.password:
        raise InvalidUserAccountCredentials

    try:
        user_account = (
            user_accounts_service.update_user_account_password_by_user_account_id(
                user_account_id=user_account.user_account_id,
                new_password=new_password,
            )
        )
    except EmptyUserAccountPasswordServiceError:
        raise EmptyUserAccountPasswordAPIError
    except IdenticalUserAccountPasswordServiceError:
        raise IdenticalUserAccountPasswordAPIError
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()

    return user_account


@router.patch(
    "/{user_account_id}/password",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": EmptyUserAccountPasswordAPIError().to_pydantic_model()
            | IdenticalUserAccountPasswordAPIError().to_pydantic_model(),
        },
    },
)
def update_user_account_password_by_user_account_id(
    user_account_id: str,
    old_password: Annotated[str, Body()],
    new_password: Annotated[str, Body()],
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_PASSWORD_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=None)
    if old_password != user_account.password:
        raise InvalidUserAccountCredentials

    try:
        user_account = (
            user_accounts_service.update_user_account_password_by_user_account_id(
                user_account_id=user_account.user_account_id,
                new_password=new_password,
            )
        )
    except EmptyUserAccountPasswordServiceError:
        raise EmptyUserAccountPasswordAPIError
    except IdenticalUserAccountPasswordServiceError:
        raise IdenticalUserAccountPasswordAPIError
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()

    return user_account


@router.patch(
    "/{user_account_id}/role",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": IdenticalUserAccountRoleAPIError(
                role=UserRole.ADMIN,
            ).to_pydantic_model(),
        },
    },
)
def update_user_account_role_by_user_account_id(
    user_account_id: str,
    role: UserRole,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_ROLE_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=None)

    old_user_account_role = user_account.role
    try:
        user_account = (
            user_accounts_service.update_user_account_role_by_user_account_id(
                user_account_id=user_account_id,
                role=role,
            )
        )
    except IdenticalUserAccountRoleServiceError:
        raise IdenticalUserAccountRoleAPIError(role=role)
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()
    for user in users_service.get_all_users():
        if user.role == old_user_account_role:
            user.role = user_account.role

    return user_account


@router.delete(
    "/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": UserAccountNotFoundAPIError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityHTTPError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def delete_user_account_by_user_account_id(
    user_account_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.DELETE_USER_ACCOUNT_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> SuccessResponseModel:
    try:
        user_accounts_service.delete_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except InvalidUserAccountIDServiceError:
        raise UserAccountNotFoundAPIError(user_account_id=user_account_id)
    try:
        user_accounts_service.write_framework_user_accounts()
    except UserAccountsFileServiceError:
        raise InternalServerErrorHTTPError()

    return SuccessResponseModel()
