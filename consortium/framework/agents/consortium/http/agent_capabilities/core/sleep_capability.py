from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import AgentMessageModel, AgentResponseModel


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
    authors = {"sekiun"}

    async def on_agent_message_sent(
        self,
        agent_message: AgentMessageModel,
    ) -> AsyncGenerator[AgentMessageModel]:
        yield agent_message

    async def on_agent_response_received(
        self,
        agent_response: AgentResponseModel,
    ) -> AsyncGenerator[AgentResponseModel]:
        yield agent_response
