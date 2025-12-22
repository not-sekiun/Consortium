import json
from functools import cached_property

from consortium.server.models.server_models import ReleaseModel
from consortium.server.server_config import CONSORTIUM_RELEASE_JSON_FILE_PATH


class ReleaseService:
    def __str__(self):
        return "Release Service"

    def __repr__(self):
        return "ReleaseService()"

    @cached_property
    def release(self):
        with CONSORTIUM_RELEASE_JSON_FILE_PATH.open("r") as file:
            return ReleaseModel(**json.load(file))
