from pydantic import BaseModel


class AgentTypeSummaryModel(BaseModel):
    name: str
    agent_type_id: str


class ListenerTypeSummaryModel(BaseModel):
    name: str
    listener_type_id: str


class ListenerTypeModel(BaseModel):
    name: str
    listener_type_id: str
    # If compatible_agent_type_ids is an empty list it is compatible with no agent
    # types.
    compatible_agent_types: list[AgentTypeSummaryModel]


class AgentTypeModel(BaseModel):
    name: str
    agent_type_id: str
    # If compatible_listener_type_ids is an empty list it is compatible with no listener
    # types.
    compatible_listener_types: list[ListenerTypeSummaryModel]
