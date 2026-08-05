import json
import pathlib
from functools import cached_property

from pydantic import ValidationError

from consortium.server.exceptions.service_exceptions.release_service_exceptions import (
    ReleaseFileEncodingError,
    ReleaseFileIsNotJSONError,
    ReleaseFileSchemaError,
    ReleaseFileSystemError,
)
from consortium.server.models.server_models import ReleaseModel
from consortium.server.utils import format_validation_error, wrap_filesystem_errors


class ReleaseService:
    def __init__(self, release_json_file: pathlib.Path):
        self._release_json_file = release_json_file

    def __str__(self):
        return "Release Service"

    def __repr__(self):
        return "ReleaseService()"

    @cached_property
    def release(self) -> ReleaseModel:
        """Loads and returns the release information from the release JSON file.

        The result is cached after the first access so the file is only read once.
        Because the property is cached, a failure here occurs on first access rather
        than at construction: a caller only sees it at the point the release
        information is first used.

        Returns:
            A parsed model containing the release metadata (e.g. version).

        Raises:
            ReleaseFileSystemError: If the release JSON file cannot be opened or read
                from disk.
            ReleaseFileEncodingError: If the release JSON file's content cannot be
                decoded as UTF-8 text.
            ReleaseFileIsNotJSONError: If the release JSON file does not contain valid
                JSON.
            ReleaseFileSchemaError: If the parsed JSON does not match the
                `ReleaseModel` schema.
        """
        with wrap_filesystem_errors(
            ReleaseFileSystemError,
            operation="read the release JSON file",
            path=self._release_json_file,
        ):
            raw_bytes = self._release_json_file.read_bytes()

        try:
            raw_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReleaseFileEncodingError(
                release_json_filepath=str(self._release_json_file),
                underlying_error=f"{type(exc).__name__}: {exc}",
            ) from exc

        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ReleaseFileIsNotJSONError(
                release_json_filepath=str(self._release_json_file),
            ) from exc

        try:
            return ReleaseModel.model_validate(parsed_json)
        except ValidationError as exc:
            raise ReleaseFileSchemaError(
                release_json_filepath=str(self._release_json_file),
                validation_error_message=format_validation_error(exc),
            ) from exc
