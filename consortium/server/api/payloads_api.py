from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.respository_api import (
    create_delete_repository_resource_by_resource_id_endpoint,
    create_download_repository_resource_by_resource_id_endpoint,
    create_get_all_repository_resources_endpoint,
    create_get_repository_resource_by_resource_id_endpoint,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.exceptions.api_exceptions.payloads_api_exceptions import (
    PayloadNotFoundError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryResourceNotFoundError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.repository_models import (
    RepositoryDirectoryModel,
    RepositoryFileModel,
)
from consortium.server.objects.user_account_objects import UserPermissions

payloads_service = server_singletons.payloads_service
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
router.add_api_route(
    path="/all",
    endpoint=create_get_all_repository_resources_endpoint(
        repository_service=payloads_service,
        get_all_repository_resources_permission=UserPermissions.READ_ALL_PAYLOADS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryFileModel | RepositoryDirectoryModel]},
    },
    name="Get All Payloads",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_repository_resource_by_resource_id_endpoint(
        repository_service=payloads_service,
        get_repository_resource_by_resource_id_permission=UserPermissions.READ_PAYLOAD_BY_PAYLOAD_ID,
        repository_resource_not_found_api_error=PayloadNotFoundError,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryDirectoryModel | RepositoryFileModel},
        404: {
            "model": PayloadNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Get Payload By Payload ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_repository_resource_by_resource_id_endpoint(
        repository_service=payloads_service,
        delete_repository_resource_by_resource_id_permission=UserPermissions.DELETE_PAYLOAD_BY_PAYLOAD_ID,
        repository_resource_not_found_api_error=PayloadNotFoundError,
    ),
    methods=["DELETE"],
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": PayloadNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Delete Payload By Payload ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_repository_resource_by_resource_id_endpoint(
        repository_service=payloads_service,
        download_repository_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_PAYLOADS,
        repository_resource_not_found_api_error=PayloadNotFoundError,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": PayloadNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Download Payload By Payload ID",
)
