from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


def _validate_duration_argument(duration: float):
    """
    Check that the duration to sleep for is greater than 0.
    """
    if duration <= 0:
        raise OptionValueValidationError(
            f"The provided duration to sleep for, '{duration}', must be a float greater "
            "than 0.",
        )


class SleepCapability(BaseAgentCapability):
    name = "sleep"
    description = "Make the agent sleep for a specified number of seconds."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    arguments = {
        SingleValueOption(
            name="duration",
            description="The duration in seconds that the agent should sleep for.",
            required=True,
            value_type=float,
            default_value=1.0,
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
