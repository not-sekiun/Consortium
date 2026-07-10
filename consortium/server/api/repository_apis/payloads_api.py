from fastapi import APIRouter
from fastapi.responses import FileResponse

import consortium.server.server_singletons as server_singletons
from consortium.server.api.repository_apis._repository_api_factory import (
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
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.consortium_exceptions import (
    repository_consortium_exceptions as consortium_excs,
)
from consortium.server.models.repository_models import PayloadModel
from consortium.server.objects.user_account_objects import UserPermissions

router = APIRouter(
    prefix="/api/payloads",
    responses={
        401: {"description": "Unauthorized"},
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
_invalid_uuid_error = InvalidUUIDError(
    resource_name="resource", uuid_value="<uuid_value>"
)

router.add_api_route(
    path="/all",
    endpoint=create_get_all_resources_endpoint(
        get_all_resources_handler=_payloads_service.get_all_payloads,
        get_all_resources_permission=UserPermissions.READ_ALL_PAYLOADS,
        response_model_class=PayloadModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": list[PayloadModel]},
    },
    name="Get All Payloads",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_get_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_payloads_service.get_payload_by_payload_id,
        get_resource_by_resource_id_permission=UserPermissions.READ_PAYLOAD_BY_PAYLOAD_ID,
        response_model_class=PayloadModel,
    ),
    methods=["GET"],
    responses={
        200: {"model": PayloadModel},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model(),
        },
    },
    name="Get Payload By Resource ID",
)
router.add_api_route(
    path="/{resource_id}",
    endpoint=create_delete_resource_by_resource_id_endpoint(
        delete_resource_by_resource_id_handler=_payloads_service.delete_payload_by_payload_id,
        delete_resource_by_resource_id_permission=UserPermissions.DELETE_PAYLOAD_BY_PAYLOAD_ID,
    ),
    status_code=204,
    responses={
        204: {},
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model(),
        },
    },
    name="Delete Payload By Resource ID",
    methods=["DELETE"],
)
router.add_api_route(
    path="/download/{resource_id}",
    endpoint=create_download_resource_by_resource_id_endpoint(
        get_resource_by_resource_id_handler=_payloads_service.get_payload_by_payload_id,
        download_resource_by_resource_id_permission=UserPermissions.DOWNLOAD_PAYLOADS,
    ),
    methods=["GET"],
    response_class=FileResponse,
    responses={
        404: {
            "model": _resource_not_found_error.to_pydantic_model(),
        },
        422: {
            "model": _invalid_uuid_error.to_pydantic_model(),
        },
    },
    name="Download Payload By Resource ID",
)
