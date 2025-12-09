from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.respository_api import (
    create_delete_repository_resource_by_resource_id_endpoint,
    create_download_repository_resource_by_resource_id_endpoint,
    create_get_all_repository_resources_endpoint,
    create_get_repository_resource_by_resource_id_endpoint,
    create_upload_repository_resource_endpoint,
)
from consortium.server.exceptions.api_exceptions.assets_api_exceptions import (
    AssetDirectoryArchiveFileFormatNotSpecifiedError,
    AssetNotFoundError,
    InvalidAssetDirectoryArchiveFileFormatError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
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

assets_service = server_singletons.assets_service
router = APIRouter(
    prefix="/api/assets",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Assets API"],
)

router.add_api_route(
    path="/all",
    endpoint=create_get_all_repository_resources_endpoint(
        repository_service=assets_service,
        get_all_repository_resources_permission=UserPermissions.READ_ALL_ASSETS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryFileModel | RepositoryDirectoryModel]},
    },
    name="Get All Assets",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_repository_resource_by_resource_id_endpoint(
        repository_service=assets_service,
        get_repository_resource_by_resource_id_permission=UserPermissions.READ_ASSET_BY_ASSET_ID,
        repository_resource_not_found_api_error=AssetNotFoundError,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryDirectoryModel | RepositoryFileModel},
        404: {
            "model": AssetNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Get Asset By Asset ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_repository_resource_by_resource_id_endpoint(
        repository_service=assets_service,
        delete_repository_resource_by_resource_id_permission=UserPermissions.DELETE_ASSET_BY_ASSET_ID,
        repository_resource_not_found_api_error=AssetNotFoundError,
    ),
    methods=["DELETE"],
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": AssetNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Delete Asset By Asset ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_repository_resource_by_resource_id_endpoint(
        repository_service=assets_service,
        download_repository_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ASSETS,
        repository_resource_not_found_api_error=AssetNotFoundError,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": AssetNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Download Asset By Asset ID",
)
router.add_api_route(
    path="/upload",
    endpoint=create_upload_repository_resource_endpoint(
        repository_service=assets_service,
        upload_repository_resource_permission=UserPermissions.UPLOAD_ASSETS,
        repository_directory_archive_file_format_not_specified_api_error=AssetDirectoryArchiveFileFormatNotSpecifiedError,
        invalid_repository_directory_archive_file_format_api_error=InvalidAssetDirectoryArchiveFileFormatError,
    ),
    methods=["POST"],
    responses={
        200: {"model": RepositoryFileModel | RepositoryDirectoryModel},
        415: {
            "model": AssetDirectoryArchiveFileFormatNotSpecifiedError().to_pydantic_model()
            | InvalidAssetDirectoryArchiveFileFormatError(
                file_format="string",
            ).to_pydantic_model(),
        },
    },
    name="Upload Asset",
)
