from collections import deque

from pydantic import BaseModel, ConfigDict, JsonValue

from consortium.client.models.alias_model import Alias
from consortium.client.models.command_info_model import CommandInfo


class BaseInterpreterContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    commands_info: dict[
        str, CommandInfo
    ] = {}  # For the `help` command to get interpreter specific help information
    aliases: dict[
        str, Alias
    ] = {}  # For the `alias` command to access and modify aliases across interpreters.
    resource_commands: deque[str] = (
        deque()
    )  # For the `rc` command to add resource commands and for interpreters to read them


class UseAgentTemplateInterpreterContext(BaseInterpreterContext):
    agent_template: dict[str, JsonValue]


class UseListenerTemplateInterpreterContext(BaseInterpreterContext):
    listener_template: dict[str, JsonValue]


class InteractAgentInterpreterContext(BaseInterpreterContext):
    agent: dict[str, JsonValue]
