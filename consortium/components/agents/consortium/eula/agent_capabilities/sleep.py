from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class SleepCapability(BaseAgentCapability):
    name = "sleep"
    description = "Put the agent to sleep for a specified duration"
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="duration",
            description="Time in seconds for the agent to sleep.",
            required=True,
            value_type=float,
            greater_than_or_equal_to=0,
        ),
    }

    async def on_execute(self):
        self.agent.mark_as_inactive()
        return (await self.recv_from_agent()).to_outcome()
