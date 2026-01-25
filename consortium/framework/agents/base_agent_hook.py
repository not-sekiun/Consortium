from enum import StrEnum

from consortium.framework.agents._agent_communicator import _AgentCommunicator


class AgentLifecycleEvent(StrEnum):
    ON_REGISTERED = "ON_REGISTERED"
    ON_CHECKED_IN = "ON_CHECKED_IN"


class BaseAgentHook(_AgentCommunicator):
    execution_triggers: AgentLifecycleEvent

    async def execute(self) -> None: ...
