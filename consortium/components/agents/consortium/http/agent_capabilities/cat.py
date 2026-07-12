from consortium.framework.agents import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption


class CatCapability(BaseAgentCapability):
    name = "cat"
    description = "Display the contents of a file"
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="path",
            description="Path to the file or directory to display.",
            required=True,
            value_type=str,
        )
    }
    mitre_attack_techniques = {"T1005"}
