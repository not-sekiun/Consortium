from datetime import datetime

from consortium.framework.agents import (
    IteratedRequestResponseCapability,
)
from consortium.framework.options import SingleValueOption


class PingCapability(IteratedRequestResponseCapability):
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

    async def resolve_iterations(self, task_launch_message):
        return task_launch_message.arguments["iterations"] - 1

    async def resolve_timeout(self, index, current_task_message):
        return self.environment.timeout

    async def on_prepare_launch(self, task_launch_message):
        self.environment.timeout = task_launch_message.arguments.pop("timeout")
        self.environment.received = 0
        self.environment.timed_out = 0
        self.environment.ping_start = datetime.now()
        self.environment.latencies = []
        return task_launch_message

    async def on_create_next_input_message(self, index, task_output_message):
        self.environment.ping_start = datetime.now()
        self.environment.task_id = task_output_message.task_id
        return self.create_task_input_message()

    async def on_response(self, index, task_output_message):
        delta = datetime.now() - self.environment.ping_start
        self.environment.received += 1
        if delta.total_seconds() < 1:
            message = (
                f"Agent returned ping response. Latency: "
                f"{delta.total_seconds() * 1000:.3f} milliseconds"
            )
        else:
            message = (
                f"Agent returned ping response. Latency: "
                f"{delta.total_seconds():.3f} seconds"
            )
        self.environment.latencies.append(delta)
        self.emit_success(message=message)
        return task_output_message, True

    async def on_timeout(self, index, current_task_message):
        delta = datetime.now() - self.environment.ping_start
        self.environment.timed_out += 1
        self.emit_failure(
            message=(
                f"Ping request timed out before agent could return ping response. "
                f"Latency: {delta.total_seconds():.3f} seconds"
            )
        )
        return None, True

    async def on_completed(self, index, task_output_message, stopped_early):
        received = self.environment.received
        timed_out = self.environment.timed_out
        total = received + timed_out
        summary = (
            f"Ping complete: {total} sent, {received} received, {timed_out} timed out."
        )
        if self.environment.latencies:
            avg_latency = sum(
                latency.total_seconds() for latency in self.environment.latencies
            ) / len(self.environment.latencies)
            summary += f" Average latency: {avg_latency * 1000:.3f} ms"
        self.emit_info(message=summary)
