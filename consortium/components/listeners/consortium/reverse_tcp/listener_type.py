from consortium.components.agents.consortium.http.agent_type import AgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType


class ListenerType(BaseListenerType):
    name = "listeners/consortium/tcp"
    compatible_agent_types = {AgentType()}


LISTENER_TYPE = ListenerType()
