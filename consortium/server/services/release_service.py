import json
import pathlib
from functools import cached_property

from consortium.server.models.server_models import ReleaseModel


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
            FileNotFoundError: If the release JSON file does not exist.
            IsADirectoryError: If the release JSON file path points to a directory
                rather than a file.
            PermissionError: If the release JSON file cannot be opened or read due
                to insufficient permissions.
            OSError: If the release JSON file cannot otherwise be opened or read.
            UnicodeDecodeError: If the release JSON file's content cannot be
                decoded as text.
            json.JSONDecodeError: If the release JSON file does not contain valid
                JSON.
            TypeError: If the release JSON file contains valid JSON that is not an
                object, since the decoded value is unpacked as keyword arguments.
            pydantic.ValidationError: If the parsed JSON does not match the
                `ReleaseModel` schema.
        """
        with self._release_json_file.open("r") as file:
            return ReleaseModel(**json.load(file))
