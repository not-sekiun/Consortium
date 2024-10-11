import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime

from consortium.framework.base_agent_capability import BaseAgentCapability, SupportedOS
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.options import SingleValueOption
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


def _validate_iterations_argument(iterations: int):
    """
    Check that the number of iterations to ping the agent, if provided, is greater than
    0.
    """
    if iterations < 1:
        raise OptionValueValidationError(
            f"The provided number of iterations to ping the agent, '{iterations}', "
            "must be an integer greater than 0.",
        )


def _validate_timeout_argument(timeout: float | None):
    """
    Check that the timeout duration, if provided, is greater than 0.
    """
    if timeout is None:
        return
    if timeout <= 0:
        raise OptionValueValidationError(
            f"The provided timeout duration, '{timeout}', must be a float greater than "
            "0.",
        )


class PingCapability(BaseAgentCapability):
    name = "ping"
    description = (
        "Ping the agent to check if it is still responsive and determine the latency "
        "of the response."
    )
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    arguments = {
        SingleValueOption(
            name="iterations",
            description="The number of times to ping the agent.",
            required=False,
            value_type=int,
            default_value=1,
            validating_function=_validate_iterations_argument,
        ),
        SingleValueOption(
            name="timeout",
            description=(
                "The duration of time in seconds to wait before considering a ping to "
                "have timed out. If not provided, there is no timeout when waiting for "
                "a ping request to return."
            ),
            required=False,
            value_type=float,
            validating_function=_validate_iterations_argument,
        ),
    }
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def handle_sending_agent_task_messages(
        self,
        agent_message: AgentTaskMessageModel,
    ) -> AsyncGenerator[AgentTaskMessageModel]:
        self.environment["response_received_event"] = asyncio.Event()
        self.environment["total_expected_pings"] = agent_message.arguments["iterations"]
        agent_message.arguments.pop("iterations")

        self.environment["ping_start_time"] = datetime.now()
        yield agent_message

        # Use the event to ensure that a new ping task is only sent to the agent after
        # the agent returned a response to the previous ping task.
        for i in range(self.environment["total_expected_pings"] - 1):
            await self.environment["response_received_event"].wait()
            self.environment["ping_start_time"] = datetime.now()
            yield agent_message
            self.environment["response_received_event"].clear()

    async def handle_receiving_agent_response_messages(
        self,
    ) -> AsyncGenerator[AgentResultMessageModel]:
        message = ""
        latencies = []

        # If iterations is not provided, only ping the agent once.
        for i in range(self.environment["total_expected_pings"]):
            latency = datetime.now() - self.environment["ping_start_time"]
            message += f"Ping {i + 1}: {latency}\n"
            latencies.append(latency)
            result_message = yield

            # As long as we are not on the last iteration, set the event to allow the
            # next ping task to be sent to the agent.
            if i < self.environment["iterations"] - 1:
                self.environment["response_received_event"].set()

        latency_sum = latencies[0]
        for latency in latencies[1:]:
            latency_sum += latency
        average_latency = latency_sum / len(latencies)
        message += f"\nAverage latency: {average_latency}"
        result_message.message = message

        yield result_message
