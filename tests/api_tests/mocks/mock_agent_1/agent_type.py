from consortium.framework.agents import BaseAgentType

from .mock_capability import MockBlockingCapability, MockCapability


class AgentType(BaseAgentType):
    name = "mock_alpha"
    agent_capabilities = {MockCapability, MockBlockingCapability}
