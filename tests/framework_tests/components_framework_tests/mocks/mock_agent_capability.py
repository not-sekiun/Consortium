from consortium.framework.agents import BaseAgentCapability, SupportedOS

from .declarations import (
    DECLARED_AUTHORS,
    DECLARED_DESCRIPTION,
    DECLARED_MITRE_TECHNIQUE,
    declared_options,
    declared_validating_function,
)

DECLARED_CAPABILITY_NAME = "mock_metadata_capability"


# BaseAgentCapability does not inherit ComponentMetadata: it carries a parallel copy of the
# same declaration and validation machinery (its own metadata model, its own options
# set-to-dict remap). It is included here because it is a major user of the declaration
# system and shares the failure modes, not because it shares the code.
class MockAgentCapability(BaseAgentCapability):
    name = DECLARED_CAPABILITY_NAME
    description = DECLARED_DESCRIPTION
    authors = set(DECLARED_AUTHORS)
    requires_admin = False
    supported_oses = {SupportedOS.WINDOWS}
    options = declared_options()
    mitre_attack_techniques = {DECLARED_MITRE_TECHNIQUE}
    validating_function = declared_validating_function
