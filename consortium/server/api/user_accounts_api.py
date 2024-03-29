from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.request_body_models import (
    NewPasswordRequestBodyModel,
    NewRoleRequestBodyModel,
    NewUserAccountRequestBodyModel,
)
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserPermissions, UserRole
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user
from consortium.server.server_exceptions import (
    DuplicateUserAccountCreationError,
    EmptyUserAccountPasswordError,
    IdenticalUserAccountPasswordError,
    IdenticalUserAccountRoleError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UserAccountNotFoundError,
)

router = APIRouter(
    prefix="/api/user-accounts",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
user_accounts_service = server_singletons.user_accounts_service
users_service = server_singletons.users_service


@router.post(
    "",
    responses={
        201: {"model": UserAccountModel},
        409: {"model": DuplicateUserAccountCreationError().to_pydantic_model()},
    },
    status_code=201,
)
async def create_user_account(
    user_account: NewUserAccountRequestBodyModel,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    str_to_enum_role_map = {
        "ADMIN": UserRole.ADMIN,
        "OPERATOR": UserRole.OPERATOR,
        "SPECTATOR": UserRole.SPECTATOR,
    }
    try:
        return user_accounts_service.create_user_account(
            username=user_account.username,
            password=user_account.password,
            # FastAPI will perform type checking against the UserRole enum since it was
            # type hinted in the function parameters hence if code execution reaches
            # this point, role is guaranteed to hold a valid value
            role=str_to_enum_role_map[user_account.role],
        )
    except ValueError:
        raise DuplicateUserAccountCreationError


@router.get(
    "/me",
    responses={
        200: {"model": UserAccountModel},
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
    },
)
async def get_own_user_account(
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_OWN_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    # For brevity reasons here we remove the so called "redundant" user_accounts key in
    # the JSON REST API output to reduce redundancy
    try:
        return user_accounts_service.get_user_account_by_username(user.username)
    # it is possible for you to delete your account while still remaining logged in
    except ValueError:
        raise UserAccountNotFoundError


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
    # For brevity reasons here we remove the so called "redundant" user_accounts
    # key in the JSON REST API output to reduce redundancy
    return user_accounts_service.get_all_user_accounts()


# Order matters, /me and /all should be put ahead of /{user_account_id} to avoid the
# /all being interpreted as a user_account_id
@router.get(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
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
    # For brevity reasons here we remove the so called "redundant" user_accounts key in
    # the JSON REST API output to reduce redundancy
    try:
        return user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except ValueError:
        raise UserAccountNotFoundError


@router.patch(
    "/me/password",
    responses={
        200: {"model": SuccessResponseModel},
        400: {
            "model": IdenticalUserAccountPasswordError().to_pydantic_model()
            | EmptyUserAccountPasswordError().to_pydantic_model(),
        },
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
    },
)
async def update_own_user_account_password(
    password: NewPasswordRequestBodyModel,
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.UPDATE_OWN_USER_ACCOUNT_PASSWORD)),
    ],
) -> SuccessResponseModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )

        if user_account.password == password.password:
            raise IdenticalUserAccountPasswordError
        if password.password == "":
            raise EmptyUserAccountPasswordError

        user_accounts_service.update_user_account_password(
            user_account=user_account,
            password=password.password,
        )
    # get_user_account_by_username() and update_user_account_password() can both raise
    # ValueError corresponding to the user account not being found
    except ValueError:
        raise UserAccountNotFoundError

    return SuccessResponseModel()


@router.patch(
    "/{user_account_id}/password",
    responses={
        200: {"model": SuccessResponseModel},
        400: {
            "model": IdenticalUserAccountPasswordError().to_pydantic_model()
            | EmptyUserAccountPasswordError().to_pydantic_model(),
        },
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
    },
)
async def update_user_account_password_by_user_account_id(
    user_account_id: str,
    # None is a sentinel value used to denote an account with no password required to
    # log in
    password: NewPasswordRequestBodyModel,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_PASSWORD_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> SuccessResponseModel:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except ValueError:
        raise UserAccountNotFoundError

    if user_account.password == password.password:
        raise IdenticalUserAccountPasswordError
    if password.password == "":
        raise EmptyUserAccountPasswordError

    user_accounts_service.update_user_account_password(
        user_account=user_account,
        password=password.password,
    )
    return SuccessResponseModel()


@router.patch(
    "/{user_account_id}/role",
    responses={
        200: {"model": SuccessResponseModel},
        400: {"model": IdenticalUserAccountRoleError().to_pydantic_model()},
    },
)
async def update_user_account_role_by_user_account_id(
    user_account_id: str,
    role: NewRoleRequestBodyModel,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(
                UserPermissions.UPDATE_USER_ACCOUNT_ROLE_BY_USER_ACCOUNT_ID,
            ),
        ),
    ],
) -> SuccessResponseModel:
    try:
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )

        if user_account.role == role.role:
            raise IdenticalUserAccountRoleError

        user_accounts_service.update_user_account_role(
            user_account=user_account,
            role=role.role,
        )
    # get_user_account_by_user_account_id() and update_user_account_role() can both
    # raise ValueError corresponding to the user account not being found
    except ValueError:
        raise UserAccountNotFoundError

    return SuccessResponseModel()


@router.delete(
    "/me",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
    },
)
async def delete_own_user_account(
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.DELETE_OWN_USER_ACCOUNT)),
    ],
) -> SuccessResponseModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )
        user_accounts_service.delete_user_account(
            user_account=user_account,
        )
    # get_user_account_by_username() and delete_user_account() can both raise ValueError
    # corresponding to the user account not being found
    except ValueError:
        raise UserAccountNotFoundError

    return SuccessResponseModel()


@router.delete(
    "/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": UserAccountNotFoundError().to_pydantic_model()},
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
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
        user_accounts_service.delete_user_account(
            user_account=user_account,
        )
    except ValueError:
        raise UserAccountNotFoundError

    return SuccessResponseModel()
