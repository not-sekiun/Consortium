# Repository API defines all the common operations that are shared between any API that
# interacts with a repository service. The repository service is responsible for
# managing the storage and retrieval of files and directories. There are three API
# endpoints that each have their own repository service to manage. They are
# `/api/assets`, `/api/artifacts`, and `/api/payload`. Each of these API endpoints
# implements all of, or a subset of the functionality described here. This is done by
# importing each factory function as required and adding its output to the router
# object.
import inspect
import os
import pathlib
import shutil
import tempfile
from collections.abc import Callable
from typing import Annotated, Any, Literal

from fastapi import Depends, Form
from fastapi.responses import FileResponse
from pydantic import UUID4
from starlette.background import BackgroundTask

from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
)
from consortium.server.exceptions.object_exceptions import (
    repository_object_exceptions as obj_excs,
)
from consortium.server.exceptions.service_exceptions import (
    repository_service_exceptions as svc_excs,
)
from consortium.server.models.repository_models import (
    RepositoryResourceModel,
)
from consortium.server.models.request_body_models import (
    UpdateRepositoryResourceRequestBodyModel,
    UploadAssetRequestBodyModel,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user


def create_get_all_resources_endpoint(
    get_all_resources_handler: Callable[[], list],
    get_all_resources_permission: UserPermissions,
    response_model_class: type[RepositoryResourceModel] = RepositoryResourceModel,
) -> Callable:
    # The return type annotation of this method is omitted because of a weird bug in
    # FastAPI's OpenAPI JSON schema generator that causes models to be duplicated if a
    # return type annotation is declared in a path operation alongside a
    # `response_model` type parameter or `responses` dictionary parameter.
    async def get_all_repository_resources(
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(get_all_resources_permission),
            ),
        ],
    ):
        return [
            response_model_class.model_validate(repository_resource.to_json())
            for repository_resource in get_all_resources_handler()
        ]

    return get_all_repository_resources


def create_get_resource_by_resource_id_endpoint(
    get_resource_by_resource_id_handler: Callable[[str], Any],
    get_resource_by_resource_id_permission: UserPermissions,
    response_model_class: type[RepositoryResourceModel] = RepositoryResourceModel,
) -> Callable:
    async def get_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(get_resource_by_resource_id_permission),
            ),
        ],
    ):
        try:
            repository_resource = get_resource_by_resource_id_handler(str(resource_id))
        except svc_excs.ResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        return response_model_class.model_validate(repository_resource.to_json())

    return get_repository_resource_by_resource_id


def create_download_resource_by_resource_id_endpoint(
    get_resource_by_resource_id_handler: Callable[[str], Any],
    download_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    # Define this function synchronously because calling `shutil.make_archive()` in an
    # async function causes event loop issues. This will signal to FastAPI that this
    # endpoint should be run in a threadpool.
    def download_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(
                    download_resource_by_resource_id_permission,
                ),
            ),
        ],
    ) -> FileResponse:
        try:
            repository_resource = get_resource_by_resource_id_handler(str(resource_id))
        except svc_excs.ResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        # Checked before any content is touched. Without this a resource whose file or
        # directory was removed from the repository directory out of band fails deeper
        # in: `shutil.make_archive` raises while packing a directory that is not there,
        # and `FileResponse` raises inside Starlette once the response is already being
        # sent, past the point where this handler could report anything at all.
        if not repository_resource.exists_on_disk:
            raise api_excs.UnsyncedRepositoryResourceError(
                resource_id=str(resource_id),
            )

        if repository_resource.is_directory:
            temp_dir = tempfile.TemporaryDirectory()
            temp_archive_file = pathlib.Path(temp_dir.name, repository_resource.name)
            shutil.make_archive(
                base_name=str(temp_archive_file.resolve()),
                format="zip",
                root_dir=repository_resource.path,
            )
            return FileResponse(
                path=str(temp_archive_file.with_suffix(".zip").resolve()),
                filename=f"{repository_resource.name}.zip"
                if repository_resource.name
                else f"{str(resource_id)}.zip",
                # Only delete the temporary directory AFTER the file has been
                # completely sent.
                background=BackgroundTask(temp_dir.cleanup),
            )
        else:
            return FileResponse(
                path=str(repository_resource.path),
                filename=repository_resource.name
                if repository_resource.name
                else str(resource_id),
            )

    return download_resource_by_resource_id


def create_upload_resource_endpoint(
    create_file_handler: Callable[..., Any],
    create_directory_handler: Callable[..., Any],
    upload_resource_permission: UserPermissions,
    response_model_class: type[RepositoryResourceModel] = RepositoryResourceModel,
) -> Callable:
    async def upload_repository_resource(
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(upload_resource_permission),
            ),
        ],
        # The uploading user is resolved here so that the REST API layer can attribute
        # the uploaded resource to the user account that uploaded it. This is the only
        # place where a resource's uploading user account is auto populated. Currently
        # only the assets API exposes an upload endpoint, whose create handlers accept a
        # `user_account_id`.
        uploading_user: Annotated[User, Depends(get_current_user)],
        upload_asset_request_body: Annotated[UploadAssetRequestBodyModel, Form()],
    ):
        file = upload_asset_request_body.file
        name = upload_asset_request_body.name
        description = upload_asset_request_body.description
        is_directory = upload_asset_request_body.is_directory
        directory_archive_file_format = (
            upload_asset_request_body.directory_archive_file_format
        )

        if is_directory:
            if directory_archive_file_format:
                file_extension = directory_archive_file_format
                filename = file.filename if file.filename is not None else ""
            else:
                # Edge case where a file (`UploadFile) is uploaded with no specified
                # filename. This can happen if the file is uploaded through a multipart
                # form with no filename parameter.
                if file.filename is None:
                    raise api_excs.RepositoryDirectoryArchiveFileFormatNotSpecifiedError
                # The file extension returned by `os.path.splitext()` as the second element
                # of the tuple is the file extension WITH the leading period.
                filename, file_extension = os.path.splitext(file.filename)
            if not file_extension:
                raise api_excs.RepositoryDirectoryArchiveFileFormatNotSpecifiedError
            # This checks primarily for zip and tar files but also does not falsely flag
            # valid archive files with multiple extensions like compressed tar archive
            # files.
            if file_extension not in (".zip", ".tar", ".gz", ".bz2", ".xz"):
                raise api_excs.RepositoryDirectoryFileNotArchiveFileError(
                    file_extension=file_extension
                )
            # Check for 'tar.bz2', 'tar.gz', and 'tar.xz' files.
            if file_extension in (".gz", ".bz2", ".xz"):
                # Again os.path.splitext splits the extension with the leading period
                # included
                filename, second_file_extension = os.path.splitext(filename)
                if second_file_extension != ".tar":
                    raise api_excs.RepositoryDirectoryFileNotArchiveFileError(
                        file_extension=file_extension
                    )
                file_extension = f"{second_file_extension}{file_extension}"

            # Type hint here to shut the IDE type checker up about the dictionary
            # values not being the expected `Literal` types.
            file_format_to_format_string: dict[
                str, Literal["zip", "tar", "gztar", "bztar", "xztar"]
            ] = {
                ".zip": "zip",
                ".tar": "tar",
                ".tar.gz": "gztar",
                ".tar.bz2": "bztar",
                ".tar.xz": "xztar",
            }
            try:
                resource = create_directory_handler(
                    content=file.file,
                    archive_file_format=file_format_to_format_string[file_extension],
                    name=name if name else file.filename,
                    description=description if description else "",
                    user_account_id=uploading_user.user_account.user_account_id,
                )
                if inspect.isawaitable(resource):
                    resource = await resource
            except obj_excs.InvalidRepositoryDirectoryArchiveFileFormatError:
                raise api_excs.InvalidRepositoryDirectoryArchiveFileFormatError() from None
        else:
            resource = create_file_handler(
                content=file.file,
                name=name if name else file.filename,
                description=description if description else "",
                user_account_id=uploading_user.user_account.user_account_id,
            )
            if inspect.isawaitable(resource):
                resource = await resource

        return response_model_class.model_validate(resource.to_json())

    return upload_repository_resource


def create_update_resource_by_resource_id_endpoint(
    update_resource_by_resource_id_handler: Callable[..., Any],
    update_resource_by_resource_id_permission: UserPermissions,
    response_model_class: type[RepositoryResourceModel] = RepositoryResourceModel,
) -> Callable:
    # Only `name` and `description` are ever forwarded to the handler here. A resource's
    # `data` (its metadata contract) is deliberately not updatable over the REST API even
    # though the underlying service methods support rebuilding it, so it is never read
    # from the request body.
    async def update_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(update_resource_by_resource_id_permission),
            ),
        ],
        update_repository_resource_request_body: UpdateRepositoryResourceRequestBodyModel,
    ):
        try:
            repository_resource = update_resource_by_resource_id_handler(
                resource_id=str(resource_id),
                name=update_repository_resource_request_body.name,
                description=update_repository_resource_request_body.description,
            )
            repository_resource = await repository_resource
        except svc_excs.ResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        return response_model_class.model_validate(repository_resource.to_json())

    return update_repository_resource_by_resource_id


def create_delete_resource_by_resource_id_endpoint(
    delete_resource_by_resource_id_handler: Callable[[str], None],
    delete_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    async def delete_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(
                    delete_resource_by_resource_id_permission,
                ),
            ),
        ],
    ):
        try:
            result = delete_resource_by_resource_id_handler(str(resource_id))
            if inspect.isawaitable(result):
                await result
        except svc_excs.ResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

    return delete_repository_resource_by_resource_id
