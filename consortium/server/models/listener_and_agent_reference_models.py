from pydantic import BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel, ListenerTypeModel


# Used for read-time references to an agent that is still live in memory (for
# example the agents currently connected to a listener). The referenced agent is
# guaranteed to exist while the reference is being built, so the full agent type
# descriptor is embedded rather than just its name.
class LiveAgentReferenceModel(BaseModel):
    agent_id: str
    name: str
    agent_type: AgentTypeModel


# Used by artifacts to store persistent references on disk to the agent that produced
# them. Records the agent type by name only: the full descriptor belongs to the live
# agent type registry and can change independently of the artifact, so a snapshot of it
# written to disk would go stale. The name is the persistent identifier for an agent
# type regardless of how the type itself evolves.
class PersistentAgentReferenceModel(BaseModel):
    agent_id: str
    name: str
    agent_type: str


# Used for read-time references to a listener that is still live in memory (the
# listener an agent is currently connected to). As with `LiveAgentReferenceModel` the
# referenced listener is guaranteed to exist while the reference is being built, so the
# full listener type descriptor is embedded rather than just its name. Listener
# references have no persistent counterpart: nothing on disk attributes a listener.
class ListenerReferenceModel(BaseModel):
    listener_id: str
    name: str
    listener_type: ListenerTypeModel
