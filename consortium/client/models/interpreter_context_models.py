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


# The staged `name` and `description` of the object the `create` command of these
# interpreters will build. They are display metadata of the object being created and are
# therefore held separately from the creating template's staged options: a template is
# free to declare its own option called `name` or `description` and those live in the
# template's `options` without ever colliding with the fields here. A `name` of `None`
# means no explicit name was staged, in which case the server generates a random one.
class UseAgentTemplateInterpreterContext(BaseInterpreterContext):
    agent_template: dict[str, JsonValue]
    agent_generator_name: str | None = None
    agent_generator_description: str = ""


class UseListenerTemplateInterpreterContext(BaseInterpreterContext):
    listener_template: dict[str, JsonValue]
    listener_name: str | None = None
    listener_description: str = ""


class InteractAgentInterpreterContext(BaseInterpreterContext):
    agent: dict[str, JsonValue]
