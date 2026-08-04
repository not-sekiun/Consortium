from datetime import datetime

from pydantic import BaseModel


class ServerConfigModel(BaseModel):
    local_host: str
    local_port: int
    remote_host_whitelist: list[str]
    remote_host_blacklist: list[str]
    server_header: str | None
    # Paths may be absolute or relative, relative paths are resolved from the project
    # root before being handed to the ASGI server.
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None
    # TODO: Implement in server and add as an option to config file
    # load_framework_plugins: bool = True
    # load_framework_listener_profiles: bool = True
    # load_framework_agent_profiles: bool = True
    # load_framework_event_hooks: bool = True


# `datetime_released` is None in the case whereby the projected datetime of a
# particular release is unknown (such as for development versions, release candidates,
# or nightly builds of the framework). This is reflected in the release.json file where
# the field is null. For every other full release, it will be a valid datetime
# object/ISO 8601 datetime string in the release.json file.
class ReleaseModel(BaseModel):
    version: str
    codename: str  # Code names are reserved for every feature release.
    datetime_released: datetime | None
