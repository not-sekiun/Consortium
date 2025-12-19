import asyncio
from datetime import datetime

from consortium.framework.agents.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
from consortium.framework.options import SingleValueOption


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
            greater_than=0,
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
            greater_than=0,
        ),
    }
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def run(
        self,
        task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        iterations = task_message.arguments["iterations"]
        timeout = task_message.arguments["timeout"]

        # Remove the iterations and timeout arguments from the agent task message to
        # prevent them from being sent to the agent. These arguments are unnecessary
        # and helps keep the ping message as minimal as possible
        task_message.arguments.pop("iterations")
        task_message.arguments.pop("timeout")

        # Send the agent task message to the agent and wait for the response. This is
        # effectively the ping.
        ping_latencies = []
        for _ in range(iterations):
            try:
                ping_started_at = datetime.now()
                if timeout is None:
                    await self.send_and_recv_from_agent(
                        task_message,
                    )
                else:
                    await asyncio.wait_for(
                        self.send_and_recv_from_agent(
                            task_message,
                        ),
                        timeout=timeout,
                    )
                ping_ended_at = datetime.now()
                ping_latencies.append(ping_ended_at - ping_started_at)
            except TimeoutError:
                ping_latencies.append(None)

        # Construct result message after aggregating all the ping latencies.
        message = "Agent pings:\n"
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
            message += "\nPing statistics:\n"
            message += (
                f"    Messages sent: {iterations} | Messages received: "
                f"{len(ping_latencies)} | Messages timed out: "
                f"{iterations - len(ping_latencies)} "
                f"({(iterations - len(ping_latencies)) / iterations * 100:.2f}% loss)\n"
            )
            message += "Latency statistics:\n"
            message += (
                f"    Maximum latency: {max(ping_latencies)} | Average latency: "
                f"{average_latency} | Minimum latency: {min(ping_latencies)}\n"
            )

        return AgentResultMessageModel(
            task_id=task_message.task_id,
            success=True,
            message=message,
            data={},
        )
