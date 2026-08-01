import json
from pathlib import Path

from consortium.client.models.client_models import Release

# File directory path related config variables. This is necessary since it allows the
# server to be portable and not rely on hardcoded file paths even if they are relative
CONSORTIUM_ROOT = Path(__file__).resolve().parents[2]
RELEASE_JSON_FILE = CONSORTIUM_ROOT / "data" / "release.json"
CLIENT_CONFIG_JSON_FILE = CONSORTIUM_ROOT / "data" / "client" / "client_config.json"
ALIASES_JSON_FILE = CONSORTIUM_ROOT / "data" / "client" / "aliases.json"
LOGGING_CONFIG_JSON_FILE = CONSORTIUM_ROOT / "data" / "client" / "logging_config.json"

# Client release information
with open(
    str(RELEASE_JSON_FILE),
) as file:
    CLIENT_RELEASE = Release(**json.load(fp=file))
