from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class RmCapability(BaseAgentCapability):
    name = "rm"
    description = "Remove files and directories on the agent."
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="path",
            description="The path to remove the contents of.",
            value_type=str,
        ),
        SingleValueOption(
            name="recursive",
            description="Whether to remove directories recursively.",
            value_type=bool,
            required=False,
            default_value=False,
        ),
        SingleValueOption(
            name="expand",
            description="Whether to expand environment variables.",
            value_type=bool,
            required=False,
            default_value=True,
        ),
    }
    mitre_attack_techniques = {"T1083"}
