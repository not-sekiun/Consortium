from datetime import datetime

from consortium.framework.agents import (
    RequestResponseCapability,
    TaskOutputMessageModel,
)
from consortium.framework.options import SingleValueOption


class PingCapability(RequestResponseCapability):
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
        )
    }

    async def resolve_timeout(self, task_message):
        return task_message.arguments["timeout"]

    async def on_request(self, task_launch_message):
        self.environment.ping_start = datetime.now()
        self.environment.task_id = task_launch_message.task_id
        task_launch_message.arguments.pop("timeout")
        return task_launch_message

    async def on_response(self, task_output_message):
        delta = datetime.now() - self.environment.ping_start
        task_output_message.message = f"Agent returned ping response. Latency: {delta.total_seconds():.3f} seconds"
        return task_output_message

    async def on_timeout(self):
        delta = datetime.now() - self.environment.ping_start
        return TaskOutputMessageModel(
            task_id=self.environment.task_id,
            success=False,
            message=(
                f"Ping request timed out before agent could return ping response. "
                f"Latency: {delta.total_seconds():.3f} seconds"
            ),
            data={},
        )
