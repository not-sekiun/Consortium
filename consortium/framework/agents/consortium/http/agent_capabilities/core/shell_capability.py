from collections.abc import AsyncGenerator

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


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
            name="blind",
            description=(
                "Execute the command blind without checking the output. This allows "
                "the launching of executables that might potentially block."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="shell_binary",
            description=(
                "The full filepath to the binary executable of the shell to use to "
                "execute the command."
            ),
            required=False,
            value_type=str,
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
    ) -> AsyncGenerator[AgentResultMessageModel]:
        result_message = yield
        yield result_message
