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
from collections.abc import Callable, Generator
from typing import Annotated, Literal

from fastapi import Depends, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from consortium.server.exceptions.api_exceptions import (
    repository_api_exceptions as repository_api_excs,
)
from consortium.server.exceptions.framework_exceptions import (
    repository_framework_exceptions as repository_framework_excs,
)
from consortium.server.exceptions.service_exceptions import (
    repository_service_exceptions as repository_svc_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.models.repository_models import (
    RepositoryDirectoryModel,
    RepositoryFileModel,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
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
        repository_resources = repository_service.get_all_repository_resources()

        repository_models = []
        for repository_resource in repository_resources:
            if isinstance(repository_resource, RepositoryDirectory):
                repository_models.append(
                    RepositoryDirectoryModel(
                        **repository_resource.to_json(),
                    ),
                )
            elif isinstance(repository_resource, RepositoryFile):
                repository_models.append(
                    RepositoryFileModel(
                        **repository_resource.to_json(),
                    ),
                )
            else:
                raise AssertionError(
                    f"Unknown repository resource type: {type(repository_resource)}"
                )
        return repository_models

    return get_all_repository_resources


def create_get_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    get_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    async def get_repository_resource_by_resource_id(
        resource_id: str,
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
                    resource_id=resource_id,
                )
            )
        except repository_svc_excs.RepositoryResourceNotFoundError as exc:
            raise repository_api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        if isinstance(repository_resource, RepositoryDirectory):
            return RepositoryDirectoryModel(
                **repository_resource.to_json(),
            )
        elif isinstance(repository_resource, RepositoryFile):
            return RepositoryFileModel(
                **repository_resource.to_json(),
            )
        else:
            raise AssertionError(
                f"Unknown repository resource type: {type(repository_resource)}"
            )

    return get_repository_resource_by_resource_id


def create_delete_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    delete_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    async def delete_repository_resource_by_resource_id(
        resource_id: str,
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
                resource_id=resource_id,
            )
        except repository_svc_excs.RepositoryResourceNotFoundError as exc:
            raise repository_api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        return SuccessResponseModel()

    return delete_repository_resource_by_resource_id


def create_download_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    download_repository_resource_by_resource_id_permission: UserPermissions,
) -> Callable:
    # Define this function synchronously because calling `shutil.make_archive()` in an
    # async function causes event loop issues. This will signal to FastAPI that this
    # endpoint should be run in a threadpool.
    def download_repository_resource_by_resource_id(
        resource_id: str,
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
            asset = repository_service.get_repository_resource_by_resource_id(
                resource_id=resource_id,
            )
        except repository_svc_excs.RepositoryResourceNotFoundError as exc:
            raise repository_api_excs.RepositoryResourceNotFoundError.from_consortium_exception(
                consortium_exception=exc,
            ) from None

        if asset.is_directory:
            temp_dir = tempfile.TemporaryDirectory()
            temp_archive_file = pathlib.Path(temp_dir.name, asset.name)
            shutil.make_archive(
                base_name=str(temp_archive_file.resolve()),
                format="zip",
                root_dir=asset.path,
            )
            return FileResponse(
                path=str(temp_archive_file.with_suffix(".zip").resolve()),
                filename=f"{asset.name}.zip"
                if asset.name
                else f"{str(asset.resource_id)}.zip",
                # Only delete the temporary directory AFTER the file has been
                # completely sent.
                background=BackgroundTask(temp_dir.cleanup),
            )
        else:
            return FileResponse(
                path=str(asset.path),
                filename=asset.name if asset.name else str(asset.resource_id),
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
        asset_directory_archive_file_format: Literal[
            ".zip",
            ".tar",
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
        ] = Form(default=None),
    ):
        def file_chunk_generator(file: UploadFile) -> Generator[bytes]:
            while chunk := file.file.read(1024):
                yield chunk

        if is_directory:
            if asset_directory_archive_file_format:
                file_extension = asset_directory_archive_file_format
                file_name = file.filename
            else:
                # The file extension returned by `os.path.splitext()` as the second element
                # of the tuple is the file extension WITH the leading period.
                file_name, file_extension = os.path.splitext(file.filename)
            if not file_extension:
                raise repository_api_excs.RepositoryDirectoryArchiveFileFormatNotSpecifiedError
            # This checks primarily for zip and tar files but also does not falsely flag
            # valid archive files with multiple extensions like compressed tar archive
            # files.
            if file_extension not in (".zip", ".tar", ".gz", ".bz2", ".xz"):
                raise repository_api_excs.RepositoryDirectoryFileNotArchiveFileError(
                    file_extension=file_extension
                )
            # Check for 'tar.bz2', 'tar.gz', and 'tar.xz' files.
            if file_extension in (".gz", ".bz2", ".xz"):
                file_name, second_file_extension = os.path.splitext(file_name)
                if second_file_extension != "tar":
                    raise repository_api_excs.RepositoryDirectoryFileNotArchiveFileError(
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
                asset = repository_service.create_repository_directory(
                    archive_file=file_chunk_generator(file),
                    name=name if name else file.filename,
                    description=description if description else "",
                    format=file_format_to_format_string[file_extension],
                )
            except repository_framework_excs.InvalidRepositoryDirectoryArchiveFileFormatError:
                raise repository_api_excs.InvalidRepositoryDirectoryArchiveFileFormatError() from None
            return RepositoryDirectoryModel(
                **asset.to_json(),
            )
        else:
            asset = repository_service.create_repository_file(
                data=file_chunk_generator(file),
                name=name if name else file.filename,
                description=description if description else "",
            )
            return RepositoryFileModel(
                **asset.to_json(),
            )

    return upload_repository_resource
