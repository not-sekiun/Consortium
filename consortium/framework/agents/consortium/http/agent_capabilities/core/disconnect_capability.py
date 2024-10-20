from collections.abc import AsyncGenerator

from consortium.framework.options import SingleValueOption
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


def _validate_duration_argument(duration: float):
    """
    Check that the duration to wait for before attempting to reconnect is greater than
    or equal to 0.
    """
    if duration < 0:
        raise OptionValueValidationError(
            "The provided duration to wait for before attempting to reconnect, "
            f"'{duration}', must be a float greater than or equal to 0.",
        )


# TODO: Provide mechanisms to allow the capability to mark the agent calling the
#  capability as disconnected.
class DisconnectCapability(BaseAgentCapability):
    name = "disconnect"
    description = "Disconnect the agent."
    arguments = {
        SingleValueOption(
            name="duration",
            description=(
                "The amount of time the agent should wait for in seconds before "
                "attempting to reconnect."
            ),
            value_type=float,
            required=False,
            default_value=0.0,
            validating_function=_validate_duration_argument,
        )
    }
    authors = {"Sekiun (github.com/not-sekiun)"}
    requires_admin = False
    supported_oses = {SupportedOS.ANY}

    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        return await self.send_agent_task_message_and_recv_agent_result_message(
            agent_task_message=agent_task_message,
        )
