from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_type_models import AgentTypeModel
from consortium.server.models.listener_and_agent_reference_models import (
    ListenerReferenceModel,
)


# `AgentStatus` lives here rather than alongside `Agent` in `agent_objects` because it
# is the serialized vocabulary of an agent's state, shared by the object that computes
# it and the model that exposes it. `agent_objects` reaches the whole framework and
# `server_singletons` through its imports, so defining the enum there forced anything
# wanting only the status vocabulary to drag all of that in with it.
class AgentStatus(StrEnum):
    # Capabilities are responsible for marking agents as ACTIVE or INACTIVE based on
    # whether the agent is connected or not. An agent can only be marked as ACTIVE or
    # INACTIVE for a listener that is currently running.
    ACTIVE = "ACTIVE"  # Running normally, attached to running listener
    INACTIVE = "INACTIVE"  # Agent was told explicitly to go inactive or lost connection

    # ORPHANED and UNREACHABLE are states inferred from the state of the attached
    # listener of an agent, the framework manages these states.
    ORPHANED = "ORPHANED"  # Attached listener temporarily not running but not deleted. For example, ERRORED or STOPPED
    UNREACHABLE = "UNREACHABLE"  # Attached listener was explicitly deleted, even if a new listener is created with the same parameters it will not recognize that agent


class AgentModel(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint: str
    agent_type: AgentTypeModel
    user: str | None
    is_admin: bool | None
    os: str | None
    version: str | None
    arch: str | None
    pid: int | None
    locale: str | None
    remote_ip: str | None
    local_ip: str | None
    hostname: str | None
    datetime_first_checked_in: str
    datetime_last_checked_in: str
    status: AgentStatus
    connected_listener: ListenerReferenceModel | None
    agent_data: dict[str, Any] | None
