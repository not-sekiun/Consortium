from consortium.framework.agents import RequestResponseCapability
from consortium.framework.options import SingleValueOption


class DisconnectCapability(RequestResponseCapability):
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

    async def on_response(self, result_message):
        self.agent.mark_as_inactive()
        return result_message
