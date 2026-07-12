from consortium.framework.agents import (
    BaseAgentCapability,
)
from consortium.framework.options import SingleValueOption


class LsCapability(BaseAgentCapability):
    name = "ls"
    description = (
        "List directory contents on the agent at the current working directory."
    )
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="path",
            description="The path to list the contents of. If not provided, the current working directory will be used.",
            required=False,
            default_value=".",
        ),
    }
    mitre_attack_techniques = {"T1083"}
