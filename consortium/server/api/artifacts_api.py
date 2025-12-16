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
from consortium.server.exceptions.service_exceptions import (
    repository_service_exceptions as svc_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.repository_models import RepositoryResourceModel
from consortium.server.objects.user_account_objects import UserPermissions

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

_artifacts_service = server_singletons.artifacts_service

_resource_not_found_error = (
    api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
        consortium_exception=svc_excs.RepositoryResourceNotFoundError(
            resource_id="<resource_id>",
        ),
    )
)

router.add_api_route(
    path="/all",
    endpoint=create_get_all_repository_resources_endpoint(
        repository_service=_artifacts_service,
        get_all_repository_resources_permission=UserPermissions.READ_ALL_ARTIFACTS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryResourceModel]},
    },
    name="Get All Artifacts",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_repository_resource_by_resource_id_endpoint(
        repository_service=_artifacts_service,
        get_repository_resource_by_resource_id_permission=UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryResourceModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Get Artifact By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_repository_resource_by_resource_id_endpoint(
        repository_service=_artifacts_service,
        delete_repository_resource_by_resource_id_permission=UserPermissions.DELETE_ARTIFACT_BY_ARTIFACT_ID,
    ),
    methods=["DELETE"],
    responses={
        200: {"model": SuccessResponseModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Delete Artifact By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_repository_resource_by_resource_id_endpoint(
        repository_service=_artifacts_service,
        download_repository_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ARTIFACTS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
    },
    name="Download Artifact By Resource ID",
)
