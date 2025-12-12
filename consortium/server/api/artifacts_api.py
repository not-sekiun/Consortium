from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.respository_api import (
    create_delete_repository_resource_by_resource_id_endpoint,
    create_download_repository_resource_by_resource_id_endpoint,
    create_get_all_repository_resources_endpoint,
    create_get_repository_resource_by_resource_id_endpoint,
)
from consortium.server.exceptions.api_exceptions.artifacts_api_exceptions import (
    ArtifactNotFoundError,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
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

artifacts_service = server_singletons.artifacts_service
router = APIRouter(
    prefix="/api/artifacts",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Artifacts API"],
)
router.add_api_route(
    path="/all",
    endpoint=create_get_all_repository_resources_endpoint(
        repository_service=artifacts_service,
        get_all_repository_resources_permission=UserPermissions.READ_ALL_ARTIFACTS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryFileModel | RepositoryDirectoryModel]},
    },
    name="Get All Artifacts",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_repository_resource_by_resource_id_endpoint(
        repository_service=artifacts_service,
        get_repository_resource_by_resource_id_permission=UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
        repository_resource_not_found_api_error=ArtifactNotFoundError,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryDirectoryModel | RepositoryFileModel},
        404: {
            "model": ArtifactNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Get Artifact By Artifact ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_repository_resource_by_resource_id_endpoint(
        repository_service=artifacts_service,
        delete_repository_resource_by_resource_id_permission=UserPermissions.DELETE_ARTIFACT_BY_ARTIFACT_ID,
        repository_resource_not_found_api_error=ArtifactNotFoundError,
    ),
    methods=["DELETE"],
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": ArtifactNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Delete Artifact By Artifact ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_repository_resource_by_resource_id_endpoint(
        repository_service=artifacts_service,
        download_repository_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ARTIFACTS,
        repository_resource_not_found_api_error=ArtifactNotFoundError,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": ArtifactNotFoundError.from_consortium_exception(
                consortium_exception=RepositoryResourceNotFoundError(
                    resource_id="string",
                ),
            ).to_pydantic_model(),
        },
    },
    name="Download Artifact By Artifact ID",
)
