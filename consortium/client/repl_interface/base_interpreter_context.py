from collections import deque

from pydantic import BaseModel

from consortium.client.models.alias_model import Alias
from consortium.client.repl_interface.base_command import BaseCommand


class BaseInterpreterContext(BaseModel):
    commands: dict[str, BaseCommand] = {}
    aliases: dict[str, Alias] = {}
    resource_commands: deque[str] = deque()
