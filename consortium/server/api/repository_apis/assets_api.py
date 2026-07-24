from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_apis._repository_api_factory import (
    create_delete_resource_by_resource_id_endpoint,
    create_download_resource_by_resource_id_endpoint,
    create_get_all_resources_endpoint,
    create_get_resource_by_resource_id_endpoint,
    create_update_resource_by_resource_id_endpoint,
    create_upload_resource_endpoint,
)
from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.service_exceptions import (
    repository_service_exceptions as svc_excs,
)
from consortium.server.models.repository_models import AssetModel
from consortium.server.models.union_response_models import (
    AssetUploadArchiveFormatErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions

router = APIRouter(
    prefix="/api/assets",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Assets"],
)

_assets_service = server_singletons.assets_service

_resource_not_found_error = (
    api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.ResourceNotFoundError(
            resource_id="<resource_id>",
        ),
    )
)
router.add_api_route(
    path="/all",
    endpoint=create_get_all_resources_endpoint(
        get_all_resources_handler=_assets_service.get_all_assets,
        get_all_resources_permission=UserPermissions.READ_ALL_ASSETS,
        response_model_class=AssetModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[AssetModel]},
    },
    name="Get All Assets",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_assets_service.get_asset_by_resource_id,
        get_resource_by_resource_id_permission=UserPermissions.READ_ASSET_BY_ASSET_ID,
        response_model_class=AssetModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": AssetModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Get Asset By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_resource_by_resource_id_endpoint(
        delete_resource_by_resource_id_handler=_assets_service.delete_asset_by_resource_id,
        delete_resource_by_resource_id_permission=UserPermissions.DELETE_ASSET_BY_ASSET_ID,
    ),
    methods=["DELETE"],
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Delete Asset By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_update_resource_by_resource_id_endpoint(
        update_resource_by_resource_id_handler=_assets_service.update_asset_by_resource_id,
        update_resource_by_resource_id_permission=UserPermissions.UPDATE_ASSET_BY_ASSET_ID,
        response_model_class=AssetModel,
    ),
    methods=["PATCH"],
    responses={
        200: {"model": AssetModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Update Asset By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_assets_service.get_asset_by_resource_id,
        download_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ASSETS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Download Asset By Resource ID",
)
router.add_api_route(
    path="/upload",
    endpoint=create_upload_resource_endpoint(
        create_file_handler=_assets_service.create_asset_file,
        create_directory_handler=_assets_service.create_asset_directory,
        upload_resource_permission=UserPermissions.UPLOAD_ASSETS,
        response_model_class=AssetModel,
    ),
    methods=["POST"],
    responses={
        200: {"model": AssetModel},
        415: {"model": AssetUploadArchiveFormatErrorResponse},
    },
    name="Upload Asset",
)
