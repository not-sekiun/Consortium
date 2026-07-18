import json
from pathlib import Path

from consortium.client.models.client_models import Release

# File directory path related config variables. This is necessary since it allows the
# server to be portable and not rely on hardcoded file paths even if they are relative
CONSORTIUM_HOME_DIRECTORY_PATH = Path(__file__).resolve().parents[2]
CONSORTIUM_RELEASE_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "release.json"
)
CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "client" / "client_config.json"
)
CONSORTIUM_ALIASES_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "client" / "aliases.json"
)
CONSORTIUM_LOGGING_CONFIG_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "data" / "client" / "logging_config.json"
)

# Client release information
with open(
    str(CONSORTIUM_RELEASE_JSON_FILE_PATH),
) as file:
    CLIENT_RELEASE = Release(**json.load(fp=file))
