import asyncio
from datetime import datetime

from consortium.framework.agents import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption


class PingCapability(BaseAgentCapability):
    name = "ping"
    description = "Ping the agent to check responsiveness and measure latency"
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="timeout",
            description="Time in seconds to wait for a response before timing out.",
            required=False,
            default_value=5.0,
            value_type=float,
            greater_than=0,
        ),
        SingleValueOption(
            name="iterations",
            description="How many ping iterations to attempt.",
            required=False,
            default_value=1,
            value_type=int,
            greater_than=0,
        ),
    }

    async def on_execute(self):
        def format_latency(seconds: float) -> str:
            return f"{seconds * 1000:.1g} ms" if seconds < 1 else f"{seconds:.3g} s"

        # Get ready message first from next agent check in before measuring latency
        await self.recv_from_agent()

        received = 0
        timed_out = 0
        for _ in range(self.task_launch_message.arguments["iterations"]):
            await asyncio.sleep(1)
            started = datetime.now()
            self.event_logger.info("Sending ping...")
            try:
                _pong = await self.send_and_recv_from_agent()
                latency_str = format_latency((datetime.now() - started).total_seconds())
                self.event_logger.success(
                    message=f"Received pong. Latency: {latency_str}"
                )
                received += 1
            except TimeoutError:
                latency_str = format_latency((datetime.now() - started).total_seconds())
                self.event_logger.failure(message=f"Ping timed out after {latency_str}")
                timed_out += 1

        total = received + timed_out
        summary = (
            f"Ping complete: {total} sent, {received} received, {timed_out} timed out."
        )
        if self.environment.latencies:
            avg_latency = sum(
                latency.total_seconds() for latency in self.environment.latencies
            ) / len(self.environment.latencies)
            avg_latency_str = format_latency(seconds=avg_latency)
            summary += f" Average latency: {avg_latency_str}"
        self.event_logger.info(message=summary)
