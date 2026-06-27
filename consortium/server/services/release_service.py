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
    def release(self):
        """Loads and returns the release information from the release JSON file.

        The result is cached after the first access so the file is only read once.

        Returns:
            ReleaseModel: A parsed model containing the release metadata (e.g. version).
        """
        with self._release_json_file.open("r") as file:
            return ReleaseModel(**json.load(file))
