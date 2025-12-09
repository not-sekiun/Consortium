from typing import Annotated

from fastapi import APIRouter, Body, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    user_accounts_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions import (
    user_accounts_service_exceptions as svc_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.request_data_models import (
    UpdateOwnUserAccountRequestDataModel,
    UpdateUserAccountByUserAccountIDRequestDataModel,
)
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserPermissions, UserRole
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

user_accounts_service = server_singletons.user_accounts_service
users_service = server_singletons.users_service
router = APIRouter(
    prefix="/api/user-accounts",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["User Accounts API"],
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
    return user_accounts_service.get_all_user_accounts()


@router.get(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": api_excs.UserAccountNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountIDNotFoundError(
                    user_account_id="string",
                ),
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
    except svc_excs.UserAccountIDNotFoundError as exc:
        raise api_excs.UserAccountNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None


@router.post(
    "",
    responses={
        201: {"model": UserAccountModel},
        422: {
            "model": api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountUsernameAlreadyExistsError.during_user_account_creation(
                    username="string",
                ),
            ).to_pydantic_model()
            | api_excs.EmptyUserAccountUsernameError.from_consortium_exception(
                consortium_exception=svc_excs.EmptyUserAccountUsernameError(),
            ).to_pydantic_model()
            | api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
                consortium_exception=svc_excs.EmptyUserAccountPasswordError(),
            ).to_pydantic_model()
            | api_excs.InvalidUserAccountRoleError.from_consortium_exception(
                consortium_exception=svc_excs.InvalidUserAccountRoleError.during_user_account_creation(
                    role="string",
                ),
            ).to_pydantic_model(),
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
        user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerErrorError() from None

    return new_user_account


@router.patch(
    "/me/username",
    responses={
        200: {"model": UserAccountModel},
        403: {"model": api_excs.UserAccountAuthenticationError().to_pydantic_model()},
        404: {
            "model": api_excs.UserAccountNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountIDNotFoundError(
                    user_account_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": api_excs.IdenticalUserAccountUsernameError.from_consortium_exception(
                consortium_exception=svc_excs.IdenticalUserAccountUsernameError(
                    username="string",
                    user_account_str="string",
                ),
            ).to_pydantic_model()
            | api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountUsernameAlreadyExistsError.during_user_account_modification(
                    username="string",
                    user_account="string",
                ),
            ).to_pydantic_model()
            | api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
                consortium_exception=svc_excs.EmptyUserAccountPasswordError(),
            ).to_pydantic_model()
            | api_excs.IdenticalUserAccountPasswordError.from_consortium_exception(
                consortium_exception=svc_excs.IdenticalUserAccountPasswordError(
                    user_account_str="string",
                ),
            ).to_pydantic_model(),
        },
    },
)
def update_own_user_account(
    request_data: UpdateOwnUserAccountRequestDataModel,
    user: Annotated[User, Depends(get_current_user)],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )
    except svc_excs.UserAccountIDNotFoundError as exc:
        raise api_excs.UserAccountNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    if request_data.username:
        old_user_account_username = user_account.username
        try:
            user_account = (
                user_accounts_service.update_user_account_username_by_user_account_id(
                    user_account_id=str(user_account.user_account_id),
                    username=request_data.username,
                )
            )
        except svc_excs.UserAccountUsernameAlreadyExistsError as exc:
            raise api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        except svc_excs.IdenticalUserAccountUsernameError as exc:
            raise api_excs.IdenticalUserAccountUsernameError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        try:
            user_accounts_service.write_framework_user_accounts()
        except svc_excs.UserAccountsFileError:
            raise InternalServerErrorError() from None
        for user in users_service.get_all_users():
            if user.username == old_user_account_username:
                user.username = user_account
    if request_data.password:
        old_password = request_data.password.old_password
        new_password = request_data.password.new_password
        if old_password != user_account.password:
            raise api_excs.UserAccountAuthenticationError

        try:
            user_account = (
                user_accounts_service.update_user_account_password_by_user_account_id(
                    user_account_id=str(user_account.user_account_id),
                    password=new_password,
                )
            )
        except svc_excs.EmptyUserAccountPasswordError as exc:
            raise api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        except svc_excs.IdenticalUserAccountPasswordError as exc:
            raise api_excs.IdenticalUserAccountPasswordError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

    return user_account


@router.patch(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": api_excs.UserAccountNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountIDNotFoundError(
                    user_account_id="string",
                ),
            ).to_pydantic_model(),
        },
        422: {
            "model": api_excs.IdenticalUserAccountUsernameError.from_consortium_exception(
                consortium_exception=svc_excs.IdenticalUserAccountUsernameError(
                    username="string",
                    user_account_str="string",
                ),
            ).to_pydantic_model()
            | api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountUsernameAlreadyExistsError.during_user_account_modification(
                    username="string",
                    user_account="string",
                ),
            ).to_pydantic_model()
            | api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
                consortium_exception=svc_excs.EmptyUserAccountPasswordError(),
            ).to_pydantic_model()
            | api_excs.IdenticalUserAccountPasswordError.from_consortium_exception(
                consortium_exception=svc_excs.IdenticalUserAccountPasswordError(
                    user_account_str="string",
                ),
            ).to_pydantic_model()
            | api_excs.IdenticalUserAccountRoleError.from_consortium_exception(
                consortium_exception=svc_excs.IdenticalUserAccountRoleError(
                    role=UserRole.ADMIN,
                    user_account_str="string",
                ),
            ).to_pydantic_model(),
        },
    },
)
def update_user_account_by_user_account_id(
    user_account_id: str,
    request_data: UpdateUserAccountByUserAccountIDRequestDataModel,
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except svc_excs.UserAccountIDNotFoundError as exc:
        raise api_excs.UserAccountNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None

    if request_data.username:
        old_user_account_username = user_account.username
        try:
            user_account = (
                user_accounts_service.update_user_account_username_by_user_account_id(
                    user_account_id=user_account_id,
                    username=request_data.username,
                )
            )
        except svc_excs.UserAccountUsernameAlreadyExistsError as exc:
            raise api_excs.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        except svc_excs.IdenticalUserAccountUsernameError as exc:
            raise api_excs.IdenticalUserAccountUsernameError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        try:
            user_accounts_service.write_framework_user_accounts()
        except svc_excs.UserAccountsFileError:
            raise InternalServerErrorError() from None
        for user in users_service.get_all_users():
            if user.username == old_user_account_username:
                user.username = request_data.username
    if request_data.password:
        try:
            user_account = (
                user_accounts_service.update_user_account_password_by_user_account_id(
                    user_account_id=user_account_id,
                    password=request_data.password,
                )
            )
        except svc_excs.EmptyUserAccountPasswordError as exc:
            raise api_excs.EmptyUserAccountPasswordError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        except svc_excs.IdenticalUserAccountPasswordError as exc:
            raise api_excs.IdenticalUserAccountPasswordError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
    if request_data.role:
        try:
            user_account = user_accounts_service.get_user_account_by_user_account_id(
                user_account_id=user_account_id,
            )
        except svc_excs.UserAccountIDNotFoundError as exc:
            raise api_excs.UserAccountNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        old_user_account_role = user_account.role
        try:
            user_account = (
                user_accounts_service.update_user_account_role_by_user_account_id(
                    user_account_id=user_account_id,
                    role=request_data.role,
                )
            )
        except svc_excs.IdenticalUserAccountRoleError as exc:
            raise api_excs.IdenticalUserAccountRoleError.from_consortium_exception(
                consortium_exception=exc,
            ) from None
        for user in users_service.get_all_users():
            if user.role == old_user_account_role:
                user.role = user_account.role

    try:
        user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerErrorError() from None

    return user_account


@router.delete(
    "/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": api_excs.UserAccountNotFoundError.from_consortium_exception(
                consortium_exception=svc_excs.UserAccountIDNotFoundError(
                    user_account_id="string",
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
    except svc_excs.UserAccountIDNotFoundError as exc:
        raise api_excs.UserAccountNotFoundError.from_consortium_exception(
            consortium_exception=exc,
        ) from None
    try:
        user_accounts_service.write_framework_user_accounts()
    except svc_excs.UserAccountsFileError:
        raise InternalServerErrorError() from None

    return SuccessResponseModel()
