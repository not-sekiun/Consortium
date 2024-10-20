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
    Check that the duration to delay agent check-ins by is greater than 0.
    """
    if duration <= 0:
        raise OptionValueValidationError(
            f"The provided duration to delay agent check-ins by, '{duration}', must be "
            "a float greater than 0.",
        )


def _validate_jitter_argument(jitter: float):
    """
    Check that the jitter to vary the agent check-in delays by is greater than 0.
    """
    if jitter <= 0:
        raise OptionValueValidationError(
            f"The provided jitter to vary agent check-in delays by, '{jitter}', must "
            "be a float greater than 0.",
        )


class DelayCapability(BaseAgentCapability):
    name = "delay"
    description = "Adjust the delay between agent check-ins."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    arguments = {
        SingleValueOption(
            name="duration",
            description=(
                "The duration in seconds that the agent should delay itself by between "
                "check-ins."
            ),
            required=True,
            value_type=float,
            default_value=1.0,
        ),
        SingleValueOption(
            name="jitter",
            description=(
                "The jitter as a percentage of the duration that the agent should "
                "randomly delay itself by between check-ins."
            ),
            required=False,
            value_type=float,
            default_value=0.0,
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
