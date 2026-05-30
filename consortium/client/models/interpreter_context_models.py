from collections import deque

from pydantic import BaseModel, ConfigDict, JsonValue

from consortium.client.models.alias_model import Alias
from consortium.client.repl_interface.base_command import BaseCommand


class BaseInterpreterContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    commands: dict[str, BaseCommand] = {}
    aliases: dict[str, Alias] = {}
    resource_commands: deque[str] = deque()


class UseAgentTemplateInterpreterContext(BaseInterpreterContext):
    agent_template: dict[str, JsonValue]


class UseListenerTemplateInterpreterContext(BaseInterpreterContext):
    listener_template: dict[str, JsonValue]


class InteractAgentInterpreterContext(BaseInterpreterContext):
    agent: dict[str, JsonValue]
