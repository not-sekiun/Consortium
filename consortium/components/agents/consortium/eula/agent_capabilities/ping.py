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

    # async def resolve_iterations(self, task_launch_message):
    #     return task_launch_message.arguments["iterations"]
    #
    # async def resolve_timeout(self, index, attempt, current_task_message):
    #     return self.environment.timeout
    #
    # async def on_prepare(self, task_launch_message):
    #     self.environment.timeout = task_launch_message.arguments.pop("timeout")
    #     self.environment.received = 0
    #     self.environment.timed_out = 0
    #     self.environment.ping_start = datetime.now()
    #     self.environment.latencies = []
    #     return task_launch_message
    #
    # async def next_task_input(self, index, task_output_message):
    #     # Sleep for 1 second between each ping to avoid accidental DoSing
    #     await asyncio.sleep(1)
    #     self.emit_info(message="Sending ping request...")
    #     self.environment.ping_start = datetime.now()
    #     self.environment.task_id = task_output_message.task_id
    #     # Return an empty task input to await the next ping output
    #     return self.create_task_input_message()
    #
    # async def on_task_output(self, index, task_output_message):
    #     # Skip the first response, that is a ready command that itself has beacon
    #     # interval latency
    #     if index == 0:
    #         return None
    #
    #     delta = datetime.now() - self.environment.ping_start
    #     self.environment.received += 1
    #     if delta.total_seconds() < 1:
    #         message = (
    #             f"Received pong response. Latency: "
    #             f"{delta.total_seconds() * 1000:.3f} milliseconds"
    #         )
    #     else:
    #         message = (
    #             f"Received pong response. Latency: {delta.total_seconds():.3f} seconds"
    #         )
    #     self.environment.latencies.append(delta)
    #     self.emit_success(message=message)
    #     return None
    #
    # async def on_timeout(self, index, attempt, current_task_message):
    #     delta = datetime.now() - self.environment.ping_start
    #     self.environment.timed_out += 1
    #     self.emit_failure(
    #         message=(
    #             f"Ping request timed out before agent could return ping response. "
    #             f"Latency: {delta.total_seconds():.3f} seconds"
    #         )
    #     )
    #     return Finish
    #
    # async def on_completed(self, index, outcome, stopped_early):
    #     received = self.environment.received
    #     timed_out = self.environment.timed_out
    #     total = received + timed_out
    #     summary = (
    #         f"Ping complete: {total} sent, {received} received, {timed_out} timed out."
    #     )
    #     if self.environment.latencies:
    #         avg_latency = sum(
    #             latency.total_seconds() for latency in self.environment.latencies
    #         ) / len(self.environment.latencies)
    #         summary += f" Average latency: {avg_latency * 1000:.3f} ms"
    #     self.emit_info(message=summary)

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
            self.emit_info("Sending ping...")
            try:
                _pong = await self.send_and_recv_from_agent()
                latency_str = format_latency((datetime.now() - started).total_seconds())
                self.emit_success(message=f"Received pong. Latency: {latency_str}")
                received += 1
            except TimeoutError:
                latency_str = format_latency((datetime.now() - started).total_seconds())
                self.emit_failure(message=f"Ping timed out after {latency_str}")
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
        self.emit_info(message=summary)
