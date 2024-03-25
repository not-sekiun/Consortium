from datetime import datetime

from pydantic import BaseModel

from consortium.server.models.user_account_models import UserAccountModel


class ServerConfigModel(BaseModel):
    local_host: str
    local_port: int
    remote_host_whitelist: list[str]
    remote_host_blacklist: list[str]
    server_banner: str


# datetime_released is None in the case whereby the projected
# datetime of a particular release is unknown (such as for development
# versions, release candidates, or nightly builds of the framework).
# This is reflected in the release.json file where the field is null.
# For every other full release, it will be a valid datetime object/ ISO 8601
# datetime string in the release.json file.
class ServerReleaseModel(BaseModel):
    version: str
    codename: str  # codenames are reserved for every feature release
    datetime_released: datetime | None


class ServerUserAccountsModel(BaseModel):
    user_accounts: list[UserAccountModel]
