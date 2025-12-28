# Repository API defines all the common operations that are shared between any API that
# interacts with a repository service. The repository service is responsible for
# managing the storage and retrieval of files and directories. There are three API
# endpoints that each have their own repository service to manage. They are
# `/api/assets`, `/api/artifacts`, and `/api/payload`. Each of these API endpoints
# implements all of, or a subset of the functionality described here. This is done by
# importing each factory function as required and adding its output to the router
# object.
import os
import pathlib
import shutil
import tempfile
from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import Depends, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import UUID4
from starlette.background import BackgroundTask

from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as api_excs,
)
from consortium.server.exceptions.consortium_exceptions import (
    repository_consortium_exceptions as consortium_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.repository_models import (
    RepositoryResourceModel,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.services.repository_service import RepositoryService


def create_get_all_repository_resources_endpoint(
    repository_service: RepositoryService,
    get_all_repository_resources_permission: UserPermissions,
) -> Callable:
    # The return type annotation of this method is omitted because of a weird bug in
    # FastAPI's OpenAPI JSON schema generator that causes models to be duplicated if a
    # return type annotation is declared in a path operation alongside a
    # `response_model` type parameter or `responses` dictionary parameter.
    async def get_all_repository_resources(
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(get_all_repository_resources_permission),
            ),
        ],
    ):
        return [
            RepositoryResourceModel(**repository_resource.to_json())
            for repository_resource in repository_service.get_all_repository_resources()
        ]

    return get_all_repository_resources


def create_get_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    get_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    async def get_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(get_repository_resource_by_resource_id_permission),
            ),
        ],
    ):
        try:
            repository_resource = (
                repository_service.get_repository_resource_by_resource_id(
                    resource_id=str(resource_id),
                )
            )
        except consortium_excs.RepositoryResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        return RepositoryResourceModel(**repository_resource.to_json())

    return get_repository_resource_by_resource_id


def create_download_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    download_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    # Define this function synchronously because calling `shutil.make_archive()` in an
    # async function causes event loop issues. This will signal to FastAPI that this
    # endpoint should be run in a threadpool.
    def download_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(
                    download_repository_resource_by_resource_id_permission,
                ),
            ),
        ],
    ) -> FileResponse:
        try:
            repository_resource = (
                repository_service.get_repository_resource_by_resource_id(
                    resource_id=str(resource_id),
                )
            )
        except consortium_excs.RepositoryResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

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
                else f"{str(repository_resource.resource_id)}.zip",
                # Only delete the temporary directory AFTER the file has been
                # completely sent.
                background=BackgroundTask(temp_dir.cleanup),
            )
        else:
            return FileResponse(
                path=str(repository_resource.path),
                filename=repository_resource.name
                if repository_resource.name
                else str(repository_resource.resource_id),
            )

    return download_repository_resource_by_resource_id


def create_upload_repository_resource_endpoint(
    repository_service: RepositoryService,
    upload_repository_resource_permission: UserPermissions,
) -> Callable:
    # Define this function synchronously because writing large files to disk in an
    # async function causes event loop issues. This will signal to FastAPI that this
    # endpoint should be run in a threadpool.
    def upload_repository_resource(
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(upload_repository_resource_permission),
            ),
        ],
        file: UploadFile,
        name: str | None = Form(default=None),
        description: str | None = Form(default=None),
        is_directory: bool = Form(...),
        directory_archive_file_format: Literal[
            ".zip",
            ".tar",
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
        ] = Form(default=None),
    ):
        if is_directory:
            if directory_archive_file_format:
                file_extension = directory_archive_file_format
                file_name = file.filename
            else:
                # The file extension returned by `os.path.splitext()` as the second element
                # of the tuple is the file extension WITH the leading period.
                file_name, file_extension = os.path.splitext(file.filename)
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
                file_name, second_file_extension = os.path.splitext(file_name)
                if second_file_extension != "tar":
                    raise api_excs.RepositoryDirectoryFileNotArchiveFileError(
                        file_extension=file_extension
                    )
                file_extension = f"{second_file_extension}.{file_extension}"

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
                resource = repository_service.create_repository_directory(
                    content=file.file,
                    archive_file_format=file_format_to_format_string[file_extension],
                    name=name if name else file.filename,
                    description=description if description else "",
                )
            except consortium_excs.InvalidRepositoryDirectoryArchiveFileFormatError:
                raise api_excs.InvalidRepositoryDirectoryArchiveFileFormatError() from None
        else:
            resource = repository_service.create_repository_file(
                content=file.file,
                name=name if name else file.filename,
                description=description if description else "",
            )

        return RepositoryResourceModel(
            **resource.to_json(),
        )

    return upload_repository_resource


def create_delete_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    delete_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    async def delete_repository_resource_by_resource_id(
        resource_id: UUID4,
        _: Annotated[
            None,
            Depends(
                AuthorizeUserRequest(
                    delete_repository_resource_by_resource_id_permission,
                ),
            ),
        ],
    ):
        try:
            repository_service.delete_repository_resource_by_resource_id(
                resource_id=str(resource_id),
            )
        except consortium_excs.RepositoryResourceNotFoundError as exc:
            raise api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        return SuccessResponseModel()

    return delete_repository_resource_by_resource_id
