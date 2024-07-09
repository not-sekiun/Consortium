from abc import ABC, abstractmethod

from consortium.server.objects.agent_objects import Agent


class BaseAgentCapability(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        command: str,
    ):
        self.name = name
        self.description = description
        self.command = command

    @abstractmethod
    def run_capability(self, agent: Agent, data: dict): ...
