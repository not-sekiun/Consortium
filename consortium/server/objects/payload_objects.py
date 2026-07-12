from typing import TYPE_CHECKING

from pydantic import JsonValue

from consortium.framework.agents import BaseAgentTemplate
from consortium.server.exceptions.service_exceptions.agent_templates_service_exceptions import (
    AgentTemplateLabelNotFoundError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)

if TYPE_CHECKING:
    from consortium.server.services.agent_templates_service import AgentTemplatesService


class Payload:
    """A view over a repository resource that adds live agent-template resolution.

    A payload wraps a "dumb" repository file or directory together with the agent
    templates service so that, on demand, the agent template that generated the payload
    can be resolved to its current live representation. The wrapped resource stores only
    an immutable point-in-time reference to the generating agent template (its label and
    name at the moment of creation), alongside the build parameters and arbitrary payload
    data; the referenced agent template may later be renamed or deleted. Resolution is
    therefore always optional and additive: it never mutates the stored reference and a
    missing agent template never invalidates the payload.

    Attribute access that is not defined on the payload itself is delegated to the wrapped
    repository resource, so a payload can be treated like the file or directory it wraps.
    """

    def __init__(
        self,
        resource: RepositoryFile | RepositoryDirectory,
        agent_templates_service: AgentTemplatesService,
    ):
        self._resource = resource
        # Held so the generating agent template reference recorded on the wrapped
        # resource can be resolved to a live agent template on demand via the
        # `resolved_agent_template` property.
        self._agent_templates_service = agent_templates_service

    def __getattr__(self, name: str):
        # Only invoked when normal attribute lookup on the payload fails. Delegates to the
        # wrapped resource so callers and the REST API can reach resource attributes
        # (path, name, is_directory, resource_id, read, etc.) directly on the payload.
        # Guard `_resource` so a lookup before it is set cannot recurse infinitely.
        if name == "_resource":
            raise AttributeError(name)
        return getattr(self._resource, name)

    def __str__(self) -> str:
        return f"Payload({self._resource})"

    def __repr__(self) -> str:
        return (
            f"Payload("
            f"resource={self._resource!r}, "
            f"agent_templates_service={self._agent_templates_service!r}"
            f")"
        )

    @property
    def resolved_agent_template(self) -> BaseAgentTemplate | None:
        """The live agent template that generated this payload, or `None` if it cannot
        be resolved.

        Resolves the generating agent template reference stored on the payload to its
        current representation by querying the agent templates service. Returns `None`
        when the payload records no generating agent template, or when the referenced
        agent template no longer exists (for example it was deleted after the payload
        was created). This is a live, additive lookup: it never mutates the stored
        reference.
        """
        agent_template_reference = self._resource.data.get("agent_template")
        if not agent_template_reference:
            return None
        label = agent_template_reference.get("label")
        if label is None:
            return None
        try:
            return self._agent_templates_service.get_agent_template_by_label(
                label=label,
            )
        except AgentTemplateLabelNotFoundError:
            return None

    def to_json(
        self, include_checksum: bool = False, force_checksum_refresh: bool = False
    ) -> dict[str, JsonValue]:
        """Serializes the payload, augmenting `data` with the resolved generating
        agent template.

        Produces the wrapped resource's JSON representation and, within its `data` field,
        adds a `resolved_agent_template` key holding the live generating agent template
        (or `None` when it cannot be resolved). The stored `data` is copied rather than
        mutated, so the resolved view never leaks into what the repository persists to
        disk.
        """
        resource_json = self._resource.to_json(
            include_checksum=include_checksum,
            force_checksum_refresh=force_checksum_refresh,
        )
        resolved_agent_template = self.resolved_agent_template
        resource_json["data"] = {
            **resource_json["data"],
            "resolved_agent_template": resolved_agent_template.to_json()
            if resolved_agent_template is not None
            else None,
        }
        return resource_json
