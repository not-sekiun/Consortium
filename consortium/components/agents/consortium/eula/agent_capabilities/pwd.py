from consortium.framework.agents import BaseAgentCapability


class PwdCapability(BaseAgentCapability):
    name = "pwd"
    description = "Print the current working directory"
    authors = {"Sekiun (github.com/not-sekiun)"}
    mitre_attack_techniques = {"T1083"}
