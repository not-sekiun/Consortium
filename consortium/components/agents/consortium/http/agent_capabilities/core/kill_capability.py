from consortium.framework.agents.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
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
