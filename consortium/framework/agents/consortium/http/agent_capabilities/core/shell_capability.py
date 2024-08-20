from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import AgentMessageModel, AgentResponseModel


class ShellCapability(BaseAgentCapability):
    name = "shell"
    description = "Execute a command using the system shell on the agent."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    arguments = {
        SingleValueOption(
            name="command",
            description="The command to execute on the agent.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="timeout",
            description=(
                "The amount of time to wait for the command to complete before timing "
                "out."
            ),
            required=False,
            value_type=int,
            default_value=10,
        ),
        SingleValueOption(
            name="shell",
            description=(
                "The full filepath to the executable of the shell to use to execute "
                "the command."
            ),
            required=False,
            value_type=str,
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
