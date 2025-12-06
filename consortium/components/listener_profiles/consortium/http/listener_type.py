from consortium.components.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.framework.listeners.base_listener_type import BaseListenerType


class ListenerType(BaseListenerType):
    name = "listeners/consortium/http"
    compatible_agent_types = {AGENT_TYPE}


LISTENER_TYPE = ListenerType()
