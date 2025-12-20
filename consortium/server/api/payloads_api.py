from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_api import (
    create_delete_repository_resource_by_resource_id_endpoint,
    create_download_repository_resource_by_resource_id_endpoint,
    create_get_all_repository_resources_endpoint,
    create_get_repository_resource_by_resource_id_endpoint,
)
from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.exceptions.consortium_exceptions import (
    repository_consortium_exceptions as consortium_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.repository_models import RepositoryResourceModel
from consortium.server.objects.user_account_objects import UserPermissions

router = APIRouter(
    prefix="/api/payloads",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Payloads API"],
)

_payloads_service = server_singletons.payloads_service

_resource_not_found_error = (
    api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.RepositoryResourceNotFoundError(
            resource_id="<resource_id>",
        ),
    )
)

router.add_api_route(
    path="/all",
    endpoint=create_get_all_repository_resources_endpoint(
        repository_service=_payloads_service,
        get_all_repository_resources_permission=UserPermissions.READ_ALL_PAYLOADS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryResourceModel]},
    },
    name="Get All Payloads",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_repository_resource_by_resource_id_endpoint(
        repository_service=_payloads_service,
        get_repository_resource_by_resource_id_permission=UserPermissions.READ_PAYLOAD_BY_PAYLOAD_ID,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryResourceModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Get Payload By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_repository_resource_by_resource_id_endpoint(
        repository_service=_payloads_service,
        delete_repository_resource_by_resource_id_permission=UserPermissions.DELETE_PAYLOAD_BY_PAYLOAD_ID,
    ),
    methods=["DELETE"],
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Delete Payload By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_repository_resource_by_resource_id_endpoint(
        repository_service=_payloads_service,
        download_repository_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_PAYLOADS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Download Payload By Resource ID",
)
