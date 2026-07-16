from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class DelayCapability(BaseAgentCapability):
    name = "delay"
    description = "Configure the delay between agent check-ins"
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="duration",
            description="Time in seconds between check-ins.",
            required=False,
            value_type=float,
            default_value=1.0,
            greater_than_or_equal_to=0,
        ),
        SingleValueOption(
            name="jitter",
            description=(
                "Random delay variance as a percentage of duration. "
                "Example: 0.5 adds +-50% randomness to timing."
            ),
            required=False,
            value_type=float,
            default_value=0.5,
            greater_than_or_equal_to=0,
        ),
    }
