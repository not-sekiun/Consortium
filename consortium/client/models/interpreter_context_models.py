from collections import deque
from dataclasses import dataclass, field

from pydantic import JsonValue

from consortium.client.models.alias_models import Alias
from consortium.client.models.command_info_model import CommandInfo


# Keep defaulted base fields keyword-only so subclasses can add required fields.
@dataclass(kw_only=True)
class BaseInterpreterContext:
    commands_info: dict[str, CommandInfo] = field(default_factory=dict)
    aliases: dict[str, Alias] = field(default_factory=dict)
    resource_commands: deque[str] = field(default_factory=deque)


@dataclass
class UseAgentTemplateInterpreterContext(BaseInterpreterContext):
    agent_template: dict[str, JsonValue]


@dataclass
class UseListenerTemplateInterpreterContext(BaseInterpreterContext):
    listener_template: dict[str, JsonValue]


@dataclass
class InteractAgentInterpreterContext(BaseInterpreterContext):
    agent: dict[str, JsonValue]
