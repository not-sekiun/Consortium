from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class DisconnectCapability(BaseAgentCapability):
    name = "disconnect"
    description = "Disconnect the agent from the server"
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="duration",
            description=(
                "Time in seconds to wait before attempting to reconnect. "
                "Set to 0 for immediate reconnection."
            ),
            value_type=float,
            required=False,
            default_value=0.0,
            greater_than_or_equal_to=0,
        ),
    }

    async def on_execute(self):
        disconnect_response = (await self.recv_from_agent()).to_outcome()
        self.agent.mark_as_inactive()
        return disconnect_response
