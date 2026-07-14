from consortium.framework.agents import BaseAgentCapability, SupportedOS
from consortium.framework.options import SingleValueOption


class ShellCapability(BaseAgentCapability):
    name = "shell"
    description = "Execute a shell command on the agent"
    authors = {"Sekiun (github.com/not-sekiun)"}
    supported_oses = SupportedOS.DESKTOP
    mitre_attack_techniques = {"T1059.001", "T1059.003", "T1059.004"}
    options = {
        SingleValueOption(
            name="command",
            description="Shell command to execute.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="timeout",
            description=(
                "Time in seconds to wait for command completion before timing out."
            ),
            required=False,
            value_type=int,
            default_value=10,
        ),
        SingleValueOption(
            name="blind",
            description=(
                "Execute a command without waiting for output. Allows launching "
                "long-running processes without blocking the agent. Timeout option "
                "will be ignored."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="shell",
            description=(
                "Path to the shell executable binary. Uses system default if not "
                "specified."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Expand environment variables in paths. Applies when changing "
                "directories."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
    }
