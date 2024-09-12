from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


class SleepCapability(BaseAgentCapability):
    name = "sleep"
    description = "Make the agent sleep for an arbitrary number of seconds."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    arguments = {
        SingleValueOption(
            name="duration",
            description="The duration in seconds that the agent should sleep for.",
            required=True,
            value_type=int,
        ),
    }
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
