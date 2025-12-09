import asyncio
from datetime import datetime

from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
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
    description = "Ping the agent."
    requires_admin = False
    supported_oses = {SupportedOS.ANY}
    options = {
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
                "a response."
            ),
            required=False,
            value_type=float,
            validating_function=_validate_timeout_argument,
        ),
    }
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        iterations = agent_task_message.arguments["iterations"]
        timeout = agent_task_message.arguments["timeout"]

        # Remove the iterations and timeout arguments from the agent task message to
        # prevent them from being sent to the agent. These arguments are unnecessary
        # and helps keep the ping message as minimal as possible
        agent_task_message.arguments.pop("iterations")
        agent_task_message.arguments.pop("timeout")

        # Send the agent task message to the agent and wait for the response. This is
        # effectively the ping.
        ping_latencies = []
        for _ in range(iterations):
            try:
                datetime_ping_started = datetime.now()
                if timeout is None:
                    _ = await self.send_agent_task_message_and_recv_agent_result_message(
                        agent_task_message,
                    )
                else:
                    await asyncio.wait_for(
                        self.send_agent_task_message_and_recv_agent_result_message(
                            agent_task_message,
                        ),
                        timeout=timeout,
                    )
                ping_ended_at = datetime.now()
                ping_latencies.append(ping_ended_at - datetime_ping_started)
            except asyncio.TimeoutError:
                ping_latencies.append(None)

        # Construct message after aggregating all the ping latencies.
        message = f"Agent pings:\n"
        for ping_index, ping_latency in enumerate(ping_latencies):
            if ping_latency is None:
                message += f"    Ping {ping_index + 1}: Timed out\n"
            else:
                message += f"    Ping {ping_index + 1}: Response received (Latency: {ping_latency})\n"

        # Calculate the average latency by only considering the pings that were
        # returned successfully
        ping_latencies = [
            ping_latency for ping_latency in ping_latencies if ping_latency is not None
        ]
        if ping_latencies:
            average_latency = sum(ping_latencies[1:], ping_latencies[0]) / len(
                ping_latencies,
            )
            message += f"\nPing statistics:\n"
            message += (
                f"    Messages sent: {iterations} | Messages received: "
                f"{len(ping_latencies)} | Messages timed out: "
                f"{iterations - len(ping_latencies)} "
                f"({(iterations - len(ping_latencies)) / iterations * 100:.2f}% loss)\n"
            )
            message += f"Latency statistics:\n"
            message += (
                f"    Maximum latency: {max(ping_latencies)} | Average latency: "
                f"{average_latency} | Minimum latency: {min(ping_latencies)}\n"
            )

        return AgentResultMessageModel(
            task_id=agent_task_message.task_id,
            success=True,
            message=message,
            data={},
        )
