from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_api import (
    create_delete_resource_by_resource_id_endpoint,
    create_download_resource_by_resource_id_endpoint,
    create_get_all_resources_endpoint,
    create_get_resource_by_resource_id_endpoint,
)
from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.consortium_exceptions import (
    repository_consortium_exceptions as consortium_excs,
)
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
        consortium_exception=consortium_excs.RepositoryResourceNotFoundError(
            resource_id="<resource_id>",
        ),
    )
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
        get_all_resources_handler=_artifacts_service.get_all_resources,
        get_all_resources_permission=UserPermissions.READ_ALL_ARTIFACTS,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[RepositoryResourceModel]},
    },
    name="Get All Artifacts",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_resource_by_resource_id_endpoint(
        delete_resource_by_resource_id_handler=_artifacts_service.delete_resource_by_resource_id,
        delete_resource_by_resource_id_permission=UserPermissions.DELETE_ARTIFACT_BY_ARTIFACT_ID,
    ),
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
    name="Delete Artifact By Resource ID",
    methods=["DELETE"],
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_artifacts_service.get_resource_by_resource_id,
        get_resource_by_resource_id_permission=UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
    ),
    methods=["GET"],
    responses={
        200: {"model": RepositoryResourceModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model()
        },
    },
    name="Get Artifact By Resource ID",
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_artifacts_service.get_resource_by_resource_id,
        download_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_ARTIFACTS,
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
    name="Download Artifact By Resource ID",
)
