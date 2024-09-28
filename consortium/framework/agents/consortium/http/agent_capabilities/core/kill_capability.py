from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


class KillCapability(BaseAgentCapability):
    name = "kill"
    description = "Kill the agent."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def handle_sending_agent_task_messages(
        self,
        agent_message: AgentTaskMessageModel,
    ) -> AsyncGenerator[AgentTaskMessageModel]:
        yield agent_message

    async def handle_receiving_agent_response_messages(
        self,
        agent_response: AgentResultMessageModel,
    ) -> AsyncGenerator[AgentResultMessageModel]:
        yield agent_response
