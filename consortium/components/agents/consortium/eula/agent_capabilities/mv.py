from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class MvCapability(BaseAgentCapability):
    name = "mv"
    description = "Move or rename files and directories on the agent."
    authors = {"Sekiun (github.com/not-sekiun)"}
    is_atomic = True
    options = {
        SingleValueOption(
            name="source",
            description="The source path to move files or directories from.",
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description="The destination path for the moved files or directories.",
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Whether to expand environment variables in the source and destination "
                "paths."
            ),
            value_type=bool,
            required=False,
            default_value=True,
        ),
    }
    mitre_attack_techniques = {"T1083"}
