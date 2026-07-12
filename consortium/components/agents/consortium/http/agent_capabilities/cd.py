from consortium.framework.agents import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption


class CdCapability(BaseAgentCapability):
    name = "cd"
    description = "Change directory on the agent"
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="path",
            description="Path to the file or directory to download.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Whether to expand environment variables in the provided path or not."
            ),
            required=False,
            value_type=bool,
            default_value=True,
        ),
    }
    mitre_attack_techniques = {"T1083"}
