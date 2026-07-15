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

For common interaction patterns, the
[`request_response_capability`][consortium.framework.agents.request_response_capability]
and
[`sequential_request_response_capability`][consortium.framework.agents.sequential_request_response_capability]
factories build capability classes without requiring a full subclass definition.
"""

from consortium.framework.agents.agent_capabilities.bidirectional_stream_capability import (
    BidirectionalStreamCapability,
)
from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_capabilities.incoming_stream_capability import (
    IncomingStreamCapability,
)
from consortium.framework.agents.agent_capabilities.iterated_request_response_capability import (
    IteratedRequestResponseCapability,
)
from consortium.framework.agents.agent_capabilities.outgoing_stream_capability import (
    OutgoingStreamCapability,
)
from consortium.framework.agents.agent_capabilities.request_response_capability import (
    RequestResponseCapability,
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
    "TaskLaunchMessageModel",
    "TaskInputMessageModel",
    "TaskOutputMessageModel",
    "BaseAgentCapability",
    "RequestResponseCapability",
    "IteratedRequestResponseCapability",
    "IncomingStreamCapability",
    "OutgoingStreamCapability",
    "Finish",
    "BidirectionalStreamCapability",
]
