# This file contains example objects that are used to parameterize pydantic models that
# are declared in the response models. These objects are solely used for displaying
# examples within the swagger UI.
from consortium.server.framework.c2_types import AgentType, ListenerType

example_listener_type = ListenerType(
    name="string",
)
example_listener_type.listener_type_id = "string"
example_listener_type.compatible_agent_type_ids = ["string"]

example_agent_type = AgentType(
    name="string",
)
example_agent_type.agent_type_id = "string"
example_agent_type.compatible_listener_type_ids = ["string"]
