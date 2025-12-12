import datetime
import json
import pathlib
import secrets

from consortium.server.models.server_models import ServerReleaseModel

# JSON Web Token generation related config variables
JSON_WEB_TOKEN_SECRET_KEY = secrets.token_hex(32)
JSON_WEB_TOKEN_ALGORITHMS = ["HS256"]
JSON_WEB_TOKEN_EXPIRATION_DURATION = datetime.timedelta(hours=24)

# File directory path related config variables. This is necessary since it allows the
# server to be portable and not rely on hardcoded file paths even if they are relative
CONSORTIUM_HOME_DIRECTORY_PATH = pathlib.Path(__file__).resolve().parents[2]
CONSORTIUM_RELEASE_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "release.json"
)
CONSORTIUM_SERVER_CONFIG_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "server_config.json"
)
CONSORTIUM_LOGGING_CONFIG_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "logging_config.json"
)
CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "user_accounts.json"
)
CONSORTIUM_SERVER_LOGS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "logs"
)
CONSORTIUM_ASSETS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "assets"
)
CONSORTIUM_ARTIFACTS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "artifacts"
)
CONSORTIUM_PAYLOADS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "server" / "payloads"
)

CONSORTIUM_COMPONENTS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "consortium" / "components"
)
CONSORTIUM_LISTENERS_DIRECTORY_PATH = CONSORTIUM_COMPONENTS_DIRECTORY_PATH / "listeners"
CONSORTIUM_AGENTS_DIRECTORY_PATH = CONSORTIUM_COMPONENTS_DIRECTORY_PATH / "agents"
CONSORTIUM_PLUGINS_DIRECTORY_PATH = CONSORTIUM_COMPONENTS_DIRECTORY_PATH / "plugins"
CONSORTIUM_EVENT_HOOKS_DIRECTORY_PATH = (
    CONSORTIUM_COMPONENTS_DIRECTORY_PATH / "event_hooks"
)

# Server release information
with open(
    str(CONSORTIUM_RELEASE_JSON_FILE_PATH),
) as file:
    SERVER_RELEASE = ServerReleaseModel(**json.load(fp=file))
