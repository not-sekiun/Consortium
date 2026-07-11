from typing import TYPE_CHECKING

from pydantic import JsonValue

from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.models.agent_models import AgentModel
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)

if TYPE_CHECKING:
    from consortium.server.services.agents_service import AgentsService


class Artifact:
    """A view over a repository resource that adds live producing-agent resolution.

    An artifact wraps a "dumb" repository file or directory together with the agents
    service so that, on demand, the agent that produced the artifact can be resolved to
    its current live representation. The wrapped resource stores only an immutable
    point-in-time reference to the producing agent (its ID, name, and type at the moment
    of creation); the referenced agent may later be deleted. Resolution is therefore
    always optional and additive: it never mutates the stored reference and a missing
    agent never invalidates the artifact.

    Attribute access that is not defined on the artifact itself is delegated to the
    wrapped repository resource, so an artifact can be treated like the file or directory
    it wraps.
    """

    def __init__(
        self,
        resource: RepositoryFile | RepositoryDirectory,
        agents_service: AgentsService,
    ):
        self._resource = resource
        # Held so the producing agent reference recorded on the wrapped resource can be
        # resolved to a live agent on demand via the `resolved_agent` property.
        self._agents_service = agents_service

    def __getattr__(self, name: str):
        # Only invoked when normal attribute lookup on the artifact fails. Delegates to
        # the wrapped resource so callers and the REST API can reach resource attributes
        # (path, name, is_directory, resource_id, read, etc.) directly on the artifact.
        # Guard `_resource` so a lookup before it is set cannot recurse infinitely.
        if name == "_resource":
            raise AttributeError(name)
        return getattr(self._resource, name)

    def __str__(self) -> str:
        return f"Artifact({self._resource})"

    def __repr__(self) -> str:
        return (
            f"Artifact("
            f"resource={self._resource!r}, "
            f"agents_service={self._agents_service!r}"
            f")"
        )

    @property
    def resolved_agent(self) -> AgentModel | None:
        """The live agent that produced this artifact, or `None` if it cannot be resolved.

        Resolves the producing agent reference stored on the artifact to its current
        representation by querying the agents service. Returns `None` when the artifact
        records no producing agent, or when the referenced agent no longer exists (for
        example it was deleted after the artifact was created). This is a live, additive
        lookup: it never mutates the stored reference.
        """
        agent_reference = self._resource.data.get("agent")
        if not agent_reference:
            return None
        agent_id = agent_reference.get("agent_id")
        if agent_id is None:
            return None
        try:
            agent = self._agents_service.get_agent_by_agent_id(agent_id=agent_id)
        except AgentNotFoundError:
            return None
        return AgentModel(**agent.to_json())

    def to_json(
        self, include_checksum: bool = False, force_checksum_refresh: bool = False
    ) -> dict[str, JsonValue]:
        """Serializes the artifact, augmenting `data` with the resolved producing agent.

        Produces the wrapped resource's JSON representation and, within its `data` field,
        adds a `resolved_agent` key holding the live producing agent (or `None` when it
        cannot be resolved). The stored `data` is copied rather than mutated, so the
        resolved view never leaks into what the repository persists to disk.
        """
        resource_json = self._resource.to_json(
            include_checksum=include_checksum,
            force_checksum_refresh=force_checksum_refresh,
        )
        resolved_agent = self.resolved_agent
        resource_json["data"] = {
            **resource_json["data"],
            "resolved_agent": resolved_agent.model_dump(mode="json")
            if resolved_agent is not None
            else None,
        }
        return resource_json
