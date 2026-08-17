"""The agents framework provides the building blocks for defining agents and the
commands they expose.

An agent is described by a [`BaseAgentType`][consortium.framework.agents.BaseAgentType],
which groups the [`BaseAgentCapability`][consortium.framework.agents.BaseAgentCapability]
commands the agent supports. Deployable agent artifacts are produced by a
[`BaseAgentGenerator`][consortium.framework.agents.BaseAgentGenerator], configured and
created through a [`BaseAgentTemplate`][consortium.framework.agents.BaseAgentTemplate].
Capabilities communicate with a live agent using the task message models
([`TaskLaunchMessageModel`][consortium.framework.agents.TaskLaunchMessageModel],
[`TaskInputMessageModel`][consortium.framework.agents.TaskInputMessageModel],
[`TaskOutputMessageModel`][consortium.framework.agents.TaskOutputMessageModel]) and
report results as a [`Success`][consortium.framework.agents.Success] or
[`Failure`][consortium.framework.agents.Failure] outcome.
"""

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    PayloadTooLargeError,
)
from consortium.framework.agents.agent_message_models import (
    Payload,
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
    SupportedOS,
)
from consortium.framework.agents.base_agent_generator import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.signal_exceptions.agent_capabilties_signal_exception import (
    AgentCapabilityLaunchError,
)

__all__ = [
    "BaseAgentGenerator",
    "BaseAgentGeneratorBuildStep",
    "BaseAgentTemplate",
    "BaseAgentType",
    "SupportedOS",
    "AgentCapabilityLaunchError",
    "Success",
    "Failure",
    "Payload",
    "PayloadTooLargeError",
    "TaskLaunchMessageModel",
    "TaskInputMessageModel",
    "TaskOutputMessageModel",
    "BaseAgentCapability",
]
