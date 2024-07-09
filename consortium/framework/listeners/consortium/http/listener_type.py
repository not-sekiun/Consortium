from consortium.framework.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.framework.c2_types import ListenerType

LISTENER_TYPE = ListenerType(
    name="listeners/consortium/http",
    compatible_agent_types={AGENT_TYPE},
)
