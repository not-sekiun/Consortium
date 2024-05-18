import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Type

from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.base_agent_template import BaseAgentTemplate
from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.framework.c2_types import AgentType, ListenerType


@dataclass
class ListenerProfile:
    listener: Type[BaseListener]
    listener_template: BaseListenerTemplate
    listener_type: ListenerType
    listener_project_folder_path: Path
    listener_profile_id: uuid.UUID = uuid.uuid4()
    name: str | None = None

    # The listener profile's name is adopted from the listener template's name. Which
    # holds all the metadata about the listener.
    def __post_init__(self):
        if self.name is None:
            self.name = self.listener_template.name

    def __str__(self):
        return f'"{self.name}" ({self.listener_profile_id})'


@dataclass
class AgentProfile:
    agent_generator: Type[BaseAgentGenerator]
    agent_template: BaseAgentTemplate
    agent_type: AgentType
    agent_project_folder_path: Path
    agent_profile_id: uuid.UUID = uuid.uuid4()
    name: str | None = None

    # The agent profile's name is adopted from the agent template's name. Which
    # holds all the metadata about the agent.
    def __post_init__(self):
        if self.name is None:
            self.name = self.agent_template.name

    def __str__(self):
        return f'"{self.name}" ({self.agent_profile_id})'
