# This file contains example objects that are used to parameterize pydantic models that
# are declared in the response models. These objects are solely used for displaying
# examples within the swagger UI.
from consortium.server.framework.c2_types import ListenerType

example_listener_type = ListenerType(
    name="string",
)
example_listener_type.listener_type_id = "string"
example_listener_type.compatible_agent_type_ids = ["string"]
