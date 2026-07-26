from consortium.framework.agents import BaseAgentCapability
from consortium.framework.options import SingleValueOption


class CpCapability(BaseAgentCapability):
    name = "cp"
    description = "Copy files and directories on the agent."
    authors = {"Sekiun (github.com/not-sekiun)"}
    options = {
        SingleValueOption(
            name="source",
            description="The source path to copy files or directories from.",
            value_type=str,
        ),
        SingleValueOption(
            name="destination",
            description="The destination path for the copied files or directories.",
            value_type=str,
        ),
        SingleValueOption(
            name="overwrite",
            description="Whether to overwrite existing files .",
            value_type=bool,
            required=False,
            default_value=False,
        ),
        SingleValueOption(
            name="recursive",
            description="Whether to copy directories recursively.",
            value_type=bool,
            required=False,
            default_value=False,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Whether to expand environment variables in source and destination "
                "paths."
            ),
            value_type=bool,
            required=False,
            default_value=True,
        ),
    }
    mitre_attack_techniques = {"T1083"}
