from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import (
    AgentCapabilityCommunicationModel,
    BaseAgentCapability,
    SupportedOS,
)
from consortium.server.models.agent_models import AgentMessageModel, AgentResponseModel


class DisconnectCapability(BaseAgentCapability):
    name = "disconnect"
    description = "Disconnect the agent."
    authors = {"sekiun"}
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    communication_model = AgentCapabilityCommunicationModel.REQUEST_RESPONSE

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
