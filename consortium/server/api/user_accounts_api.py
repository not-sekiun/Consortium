from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.request_body_models import (
    NewUserAccountAttributesRequestBodyModel,
    NewUserAccountRequestBodyModel,
)
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserPermissions, UserRole
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user
from consortium.server.server_exceptions import (
    EmptyUserAccountPasswordError,
    ForbiddenError,
    IdenticalUserAccountPasswordError,
    IdenticalUserAccountRoleError,
    IdenticalUserAccountUsernameError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UserAccountNotFoundError,
    UserAccountUsernameAlreadyExistsError,
)

router = APIRouter(
    prefix="/api/user-accounts",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
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
        422: {
            "model": IdenticalUserAccountUsernameError(
                username="string",
            ).to_pydantic_model()
            | EmptyUserAccountPasswordError().to_pydantic_model(),
        },
    },
    status_code=201,
)
async def create_user_account(
    new_user_account: NewUserAccountRequestBodyModel,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.CREATE_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    if not new_user_account.password:
        raise EmptyUserAccountPasswordError

    str_to_enum_role_map = {
        "ADMIN": UserRole.ADMIN,
        "OPERATOR": UserRole.OPERATOR,
        "SPECTATOR": UserRole.SPECTATOR,
    }
    try:
        return user_accounts_service.create_user_account(
            username=new_user_account.username,
            password=new_user_account.password,
            # FastAPI will perform type checking against the UserRole enum since it was
            # type hinted in the function parameters hence if code execution reaches
            # this point, role is guaranteed to hold a valid value
            role=str_to_enum_role_map[new_user_account.role],
        )
    except ValueError:
        raise IdenticalUserAccountUsernameError


@router.get(
    "/me",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
    },
)
async def get_own_user_account(
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_OWN_USER_ACCOUNT)),
    ],
) -> UserAccountModel:
    try:
        return user_accounts_service.get_user_account_by_username(user.username)
    # It is possible for you to delete your user account while still remaining logged
    # in. We indicate this to the exception by setting user_account_id to None.
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=None)


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
    # We remove the user_accounts key in the JSON REST API output to reduce redundancy
    return user_accounts_service.get_all_user_accounts()


# Order matters, /me and /all should be put ahead of /{user_account_id} to avoid the
# /all being interpreted as a user_account_id
@router.get(
    "/{user_account_id}",
    responses={
        200: {"model": UserAccountModel},
        404: {
            "model": UserAccountNotFoundError(
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
    # For brevity reasons here we remove the so called "redundant" user_accounts key in
    # the JSON REST API output to reduce redundancy
    try:
        return user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=user_account_id)


@router.patch(
    "/me",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": UserAccountNotFoundError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": IdenticalUserAccountUsernameError(
                username="string",
            ).to_pydantic_model()
            | UserAccountUsernameAlreadyExistsError(
                username="string",
            ).to_pydantic_model()
            | IdenticalUserAccountPasswordError().to_pydantic_model()
            | EmptyUserAccountPasswordError().to_pydantic_model()
            | IdenticalUserAccountRoleError(role=UserRole.ADMIN).to_pydantic_model(),
        },
    },
)
async def update_own_user_account(
    updated_user_account_attributes: NewUserAccountAttributesRequestBodyModel,
    user: Annotated[User, Depends(get_current_user)],
) -> UserAccountModel:
    try:
        user_account = user_accounts_service.get_user_account_by_username(
            username=user.username,
        )
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=None)

    new_username = updated_user_account_attributes.username
    new_password = updated_user_account_attributes.password
    new_role = updated_user_account_attributes.role

    # Manually perform permission checks here because several logically related
    # operations that each individually may require different permission levels are
    # grouped together here in a manner that is not supported by the permission
    # checking system that uses dependency injection. In particular, users with the
    # OPERATOR role are able to change their own usernames and passwords but not their
    # roles.
    if (
        (
            new_username
            and UserPermissions.UPDATE_OWN_USER_ACCOUNT_USERNAME
            not in AuthorizeUserRequest.ROLE_PERMISSIONS[user.role]
        )
        or (
            new_password
            and UserPermissions.UPDATE_OWN_USER_ACCOUNT_PASSWORD
            not in AuthorizeUserRequest.ROLE_PERMISSIONS[user.role]
        )
        or (
            new_role
            and UserPermissions.UPDATE_OWN_USER_ACCOUNT_ROLE
            not in AuthorizeUserRequest.ROLE_PERMISSIONS[user.role]
        )
    ):
        raise ForbiddenError

    if new_username and new_username == user_account.username:
        raise IdenticalUserAccountUsernameError(username=new_username)
    if new_password == "":
        raise EmptyUserAccountPasswordError
    if new_password and new_password == user_account.password:
        raise IdenticalUserAccountPasswordError
    if new_role and new_role == user_account.role:
        raise IdenticalUserAccountRoleError(role=user_account.role)

    # We perform all pre-checks before updating the user account to avoid partial
    # updates in case of an exception due to errors in any of the provided attributes.
    # Errors should not be raised in this section since we performed all the pre-checks.
    if new_username is not None:
        try:
            user_accounts_service.update_user_account_username(
                user_account=user_account,
                username=new_username,
            )
        # Given that we performed the pre-check to see if the user exists the only
        # ValueError that can be raised here is if the username already exists.
        except ValueError:
            raise UserAccountUsernameAlreadyExistsError(username=new_username)
    if new_password is not None:
        user_accounts_service.update_user_account_password(
            user_account=user_account,
            password=new_password,
        )
    if new_role is not None:
        user_accounts_service.update_user_account_role(
            user_account=user_account,
            role=new_role,
        )

    return user_account


@router.patch(
    "/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": UserAccountNotFoundError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
        422: {
            "model": IdenticalUserAccountUsernameError(
                username="string",
            ).to_pydantic_model()
            | UserAccountUsernameAlreadyExistsError(
                username="string",
            ).to_pydantic_model()
            | IdenticalUserAccountPasswordError().to_pydantic_model()
            | EmptyUserAccountPasswordError().to_pydantic_model()
            | IdenticalUserAccountRoleError(role=UserRole.ADMIN).to_pydantic_model(),
        },
    },
)
async def update_user_account_by_user_account_id(
    user_account_id: str,
    updated_user_account_attributes: NewUserAccountAttributesRequestBodyModel,
    # Manual permissions checking not necessary because the same granularity for each
    # permission is not required here. If you are able to update any one attribute for
    # another user it makes sense for you to be able to update all attributes for that
    # user.
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
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=None)

    new_username = updated_user_account_attributes.username
    new_password = updated_user_account_attributes.password
    new_role = updated_user_account_attributes.role

    if new_username and new_username == user_account.username:
        raise IdenticalUserAccountUsernameError(username=new_username)
    if new_password == "":
        raise EmptyUserAccountPasswordError
    if new_password and new_password == user_account.password:
        raise IdenticalUserAccountPasswordError
    if new_role and new_role == user_account.role:
        raise IdenticalUserAccountRoleError(role=user_account.role)

    # We perform all pre-checks before updating the user account to avoid partial
    # updates in case of an exception due to errors in any of the provided attributes.
    # Errors should not be raised in this section since we performed all the pre-checks.
    if new_username is not None:
        try:
            user_accounts_service.update_user_account_username(
                user_account=user_account,
                username=new_username,
            )
        except ValueError:
            raise UserAccountUsernameAlreadyExistsError(username=new_username)
    if new_password is not None:
        user_accounts_service.update_user_account_password(
            user_account=user_account,
            password=new_password,
        )
    if new_role is not None:
        user_accounts_service.update_user_account_role(
            user_account=user_account,
            role=new_role,
        )

    return user_account


@router.delete(
    "/me",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": UserAccountNotFoundError(
                user_account_id="string",
            ).to_pydantic_model(),
        },
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
    # corresponding to the user account not being found.
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=None)

    return SuccessResponseModel()


@router.delete(
    "/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": UserAccountNotFoundError(
                user_account_id="string",
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
        user_account = user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
        user_accounts_service.delete_user_account(
            user_account=user_account,
        )
    except ValueError:
        raise UserAccountNotFoundError(user_account_id=user_account_id)

    return SuccessResponseModel()
