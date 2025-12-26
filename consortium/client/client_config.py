import json
from pathlib import Path

from consortium.client.models.client_models import Release

# File directory path related config variables. This is necessary since it allows the
# server to be portable and not rely on hardcoded file paths even if they are relative
CONSORTIUM_HOME_DIRECTORY_PATH = Path(__file__).resolve().parents[2]
CONSORTIUM_RELEASE_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "content" / "release.json"
)
CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "content" / "client" / "client_config.json"
)
CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "content" / "client" / "logs"
)
CONSORTIUM_COMMAND_ALIASES_JSON_FILE_PATH = (
    CONSORTIUM_HOME_DIRECTORY_PATH / "content" / "client" / "command_aliases.json"
)

# Client release information
with open(
    str(CONSORTIUM_RELEASE_JSON_FILE_PATH),
) as file:
    CLIENT_RELEASE = Release(**json.load(fp=file))
