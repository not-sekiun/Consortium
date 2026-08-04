from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_apis._repository_api_factory import (
    create_delete_resource_by_resource_id_endpoint,
    create_download_resource_by_resource_id_endpoint,
    create_get_all_resources_endpoint,
    create_get_resource_by_resource_id_endpoint,
    create_update_resource_by_resource_id_endpoint,
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
from consortium.server.models.repository_models import ArtifactModel
from consortium.server.models.union_response_models import (
    RepositoryDownloadServerErrorResponse,
    RequestValidationErrorResponse,
)
from consortium.server.objects.user_account_objects import UserPermissions

router = APIRouter(
    prefix="/api/artifacts",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Artifacts"],
)

_artifacts_service = server_singletons.artifacts_service

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
        get_all_resources_handler=_artifacts_service.get_all_artifacts,
        get_all_resources_permission=UserPermissions.READ_ALL_ARTIFACTS,
        response_model_class=ArtifactModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[ArtifactModel]},
    },
    name="Get All Artifacts",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_resource_by_resource_id_endpoint(
        delete_resource_by_resource_id_handler=_artifacts_service.delete_artifact_by_resource_id,
        delete_resource_by_resource_id_permission=UserPermissions.DELETE_ARTIFACT_BY_ARTIFACT_ID,
    ),
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Delete Artifact By Resource ID",
    methods=["DELETE"],
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_artifacts_service.get_artifact_by_resource_id,
        get_resource_by_resource_id_permission=UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
        response_model_class=ArtifactModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": ArtifactModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Get Artifact By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_update_resource_by_resource_id_endpoint(
        update_resource_by_resource_id_handler=_artifacts_service.update_artifact_by_resource_id,
        update_resource_by_resource_id_permission=UserPermissions.UPDATE_ARTIFACT_BY_ARTIFACT_ID,
        response_model_class=ArtifactModel,
    ),
    methods=["PATCH"],
    responses={
        200: {"model": ArtifactModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
    },
    name="Update Artifact By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_artifacts_service.get_artifact_by_resource_id,
        download_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ARTIFACTS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {"model": RequestValidationErrorResponse},
        500: {"model": RepositoryDownloadServerErrorResponse},
    },
    name="Download Artifact By Resource ID",
)
