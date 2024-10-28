from consortium.framework.c2_types import BaseAgentType, BaseListenerType


class ListenerType(BaseListenerType):
    name = "listeners/consortium/http"


class AgentType(BaseAgentType):
    name = "agents/consortium/http"
    compatible_listener_types = {ListenerType()}


print(ListenerType().get_all_compatible_agent_types())
print(AgentType().get_all_compatible_listener_types())
