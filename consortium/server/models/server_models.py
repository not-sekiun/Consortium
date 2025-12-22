from datetime import datetime

from pydantic import BaseModel


# `datetime_released` is None in the case whereby the projected datetime of a
# particular release is unknown (such as for development versions, release candidates,
# or nightly builds of the framework). This is reflected in the release.json file where
# the field is null. For every other full release, it will be a valid datetime
# object/ISO 8601 datetime string in the release.json file.
class ReleaseModel(BaseModel):
    version: str
    codename: str  # Code names are reserved for every feature release.
    datetime_released: datetime | None
