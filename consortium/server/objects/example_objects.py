# This file contains example objects that are used to parameterize pydantic models that
# are declared in the response models. These objects are solely used for displaying
# examples within the swagger UI.
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType


# TODO: Trash this entirely once we move off from the old agent/listener type system.
class _ExampleListenerType(BaseListenerType):
    name = "<listener_type_name>"


class _ExampleAgentType(BaseAgentType):
    name = "<agent_type_name>"


example_listener_type = _ExampleListenerType()
example_listener_type.listener_type_id = "string"
example_listener_type.compatible_agent_type_ids = ["string"]

example_agent_type = _ExampleAgentType()
example_agent_type.agent_type_id = "string"
example_agent_type.compatible_listener_type_ids = ["string"]
