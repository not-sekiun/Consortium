# Repository API defines all the common operations that are shared between any API that
# interacts with a repository service. The repository service is responsible for
# managing the storage and retrieval of files and directories. There are three API
# endpoints that each have their own repository service to manage. They are
# `/api/assets`, `/api/artifacts`, and `/api/payload`. Each of these API endpoints
# implements all of, or a subset of the functionality described here. This is done by
# importing each factory function as required and adding its output to the router
# object.
import os
import shutil
import tempfile
from collections.abc import Generator
from typing import Annotated, Callable, Literal, Type

from fastapi import Depends, Form, UploadFile
from fastapi.responses import FileResponse

from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError
from consortium.server.exceptions.api_exceptions.repository_api_exceptions import (
    InvalidRepositoryDirectoryArchiveFileFormatError,
    RepositoryDirectoryArchiveFileFormatNotSpecifiedError,
)
from consortium.server.exceptions.service_exceptions.repository_service_exceptions import (
    RepositoryResourceNotFoundError,
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
                assert (
                    False
                ), f"Unknown repository resource type: {type(repository_resource)}"
        return repository_models

    return get_all_repository_resources


def create_get_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    get_repository_resource_by_resource_id_permission: UserPermissions,
    repository_resource_not_found_api_error: Type[NotFoundError],
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
        except RepositoryResourceNotFoundError as exc:
            raise repository_resource_not_found_api_error.from_service_exception(
                service_exception=exc,
            )

        if isinstance(repository_resource, RepositoryDirectory):
            return RepositoryDirectoryModel(
                **repository_resource.to_json(),
            )
        elif isinstance(repository_resource, RepositoryFile):
            return RepositoryFileModel(
                **repository_resource.to_json(),
            )
        else:
            assert (
                False
            ), f"Unknown repository resource type: {type(repository_resource)}"

    return get_repository_resource_by_resource_id


def create_delete_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    delete_repository_resource_by_resource_id_permission: UserPermissions,
    repository_resource_not_found_api_error: Type[NotFoundError],
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
        except RepositoryResourceNotFoundError as exc:
            raise repository_resource_not_found_api_error.from_service_exception(
                service_exception=exc,
            )

        return SuccessResponseModel()

    return delete_repository_resource_by_resource_id


def create_download_repository_resource_by_resource_id_endpoint(
    repository_service: RepositoryService,
    download_repository_resource_by_resource_id_permission: UserPermissions,
    repository_resource_not_found_api_error: Type[NotFoundError],
) -> Callable:
    async def download_repository_resource_by_resource_id(
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
        except RepositoryResourceNotFoundError as exc:
            raise repository_resource_not_found_api_error.from_service_exception(
                service_exception=exc,
            )

        if asset.is_directory:
            with tempfile.TemporaryDirectory() as temp_dir_path:
                shutil.make_archive(
                    base_name=asset.name,
                    format="zip",
                    root_dir=temp_dir_path,
                    base_dir=asset.path,
                )
                return FileResponse(
                    path=str(asset.path),
                    filename=asset.name if asset.name else str(asset.resource_id),
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
    repository_directory_archive_file_format_not_specified_api_error: Type[
        RepositoryDirectoryArchiveFileFormatNotSpecifiedError
    ],
    invalid_repository_directory_archive_file_format_api_error: Type[
        InvalidRepositoryDirectoryArchiveFileFormatError
    ],
) -> Callable:
    async def upload_repository_resource(
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
        def file_chunk_generator(file: UploadFile) -> Generator[bytes, None, None]:
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
                raise repository_directory_archive_file_format_not_specified_api_error
            # This checks primarily for zip and tar files but also does not falsely flag
            # valid archive files with multiple extensions like compressed tar archive
            # files.
            if file_extension not in (".zip", ".tar", ".gz", ".bz2", ".xz"):
                raise invalid_repository_directory_archive_file_format_api_error(
                    file_format=file_extension,
                )
            # Check for 'tar.bz2', 'tar.gz', and 'tar.xz' files.
            if file_extension in (".gz", ".bz2", ".xz"):
                file_name, second_file_extension = os.path.splitext(file_name)
                if second_file_extension != "tar":
                    raise invalid_repository_directory_archive_file_format_api_error(
                        file_format=file_extension,
                    )
                file_extension = f"{second_file_extension}.{file_extension}"

            file_format_to_format_string = {
                ".zip": "zip",
                ".tar": "tar",
                ".tar.gz": "gztar",
                ".tar.bz2": "bztar",
                ".tar.xz": "xztar",
            }
            asset = repository_service.create_repository_directory(
                archive_file=file_chunk_generator(file),
                name=name if name else file.filename,
                description=description if description else "",
                format=file_format_to_format_string[file_extension],
            )
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
