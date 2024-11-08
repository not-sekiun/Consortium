from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
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
                "the launching of long running executables without blocking the agent."
                "The timeout option will not apply when this option is set."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="shell",
            description=(
                "The filepath to the binary executable of the shell to use to execute "
                "the provided command."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Attempt to expand environment variables when provided while changing "
                "directories. By default, this is disabled."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
    }
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        return await self.send_agent_task_message_and_recv_agent_result_message(
            agent_task_message=agent_task_message,
        )
