from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_apis._repository_api_factory import (
    create_delete_resource_by_resource_id_endpoint,
    create_download_resource_by_resource_id_endpoint,
    create_get_all_resources_endpoint,
    create_get_resource_by_resource_id_endpoint,
    create_upload_resource_endpoint,
)
from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
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
    repository_service_exceptions as consortium_excs,
)
from consortium.server.models.repository_models import AssetModel
from consortium.server.objects.user_account_objects import UserPermissions

router = APIRouter(
    prefix="/api/assets",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Assets API"],
)

_assets_service = server_singletons.assets_service

_resource_not_found_error = (
    api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
        consortium_exception=consortium_excs.RepositoryResourceNotFoundError(
            resource_id="<resource_id>",
        ),
    )
)
_invalid_resource_directory_archive_file_format_error = (
    api_excs.InvalidRepositoryDirectoryArchiveFileFormatError()
)
_resource_directory_archive_file_format_not_specified_error = (
    api_excs.RepositoryDirectoryArchiveFileFormatNotSpecifiedError()
)
_repository_directory_file_not_archive_file_error = (
    api_excs.RepositoryDirectoryFileNotArchiveFileError()
)
_invalid_uuid_error = InvalidUUIDError(
    resource_name="resource", uuid_value="<uuid_value>"
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}]
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
        get_resource_by_resource_id_handler=_assets_service.get_asset_by_asset_id,
        get_resource_by_resource_id_permission=UserPermissions.READ_ASSET_BY_ASSET_ID,
        response_model_class=AssetModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": AssetModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
    name="Get Asset By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_resource_by_resource_id_endpoint(
        delete_resource_by_resource_id_handler=_assets_service.delete_asset_by_asset_id,
        delete_resource_by_resource_id_permission=UserPermissions.DELETE_ASSET_BY_ASSET_ID,
    ),
    methods=["DELETE"],
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
    name="Delete Asset By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_assets_service.get_asset_by_asset_id,
        download_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ASSETS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
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
        415: {
            "model": _resource_directory_archive_file_format_not_specified_error.to_pydantic_model()
            | _invalid_resource_directory_archive_file_format_error.to_pydantic_model()
            | _repository_directory_file_not_archive_file_error.to_pydantic_model()
        },
    },
    name="Upload Asset",
)
