from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


# TODO: Provide mechanisms to allow the capability to mark the agent as dead.
class KillCapability(BaseAgentCapability):
    name = "kill"
    description = "Kill the agent."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        return await self.send_agent_task_message_and_recv_agent_result_message(
            agent_task_message=agent_task_message,
        )
