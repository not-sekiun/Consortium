from consortium.framework.agents.consortium.http.agent_type import AgentType
from consortium.framework.c2_types import BaseListenerType


class ListenerType(BaseListenerType):
    name = "listeners/consortium/http"
    compatible_agent_types = {AgentType()}


LISTENER_TYPE = ListenerType()
