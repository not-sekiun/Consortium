import uuid
from pathlib import Path

# Rename packaging.version import to prevent type hint conflict with .version property
# on `ListenerProfile` and `AgentProfile`
from packaging import (
    specifiers,
    version as packaging_version,
)

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener import BaseListener
from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.framework.listeners.base_listener_type import BaseListenerType


class ListenerProfile:
    def __init__(
        self,
        listener: type[BaseListener],
        listener_template: BaseListenerTemplate,
        listener_type: BaseListenerType,
    ):
        self.listener_profile_id = uuid.uuid4()
        self.listener = listener
        self.listener_template = listener_template
        self.listener_type = listener_type

    def __str__(self):
        return f"'{self.name}' ({self.listener_profile_id})"

    def __repr__(self):
        return (
            f"ListenerProfile("
            f"listener={self.listener!r}, "
            f"listener_template={self.listener_template!r}, "
            f"listener_type={self.listener_type!r}"
            f")"
        )

    @property
    def label(self) -> str:
        return self.listener_template.label

    @property
    def name(self) -> str | None:
        return self.listener_template.name

    @property
    def description(self) -> str:
        return self.listener_template.description

    @property
    def version(self) -> packaging_version.Version | None:
        return self.listener_template.version

    @property
    def compatible_framework_version(self) -> specifiers.SpecifierSet | None:
        return self.listener_template.compatible_framework_version

    @property
    def authors(self) -> set[str]:
        return self.listener_template.authors

    @property
    def component_dependencies(self) -> set[str]:
        return self.listener_template.component_dependencies

    @property
    def listener_project_folder(self) -> Path:
        return self.listener_template.listener_project_folder


class AgentProfile:
    def __init__(
        self,
        agent_generator: type[BaseAgentGenerator],
        agent_template: BaseAgentTemplate,
        agent_type: BaseAgentType,
    ):
        self.agent_profile_id = uuid.uuid4()
        self.agent_generator = agent_generator
        self.agent_template = agent_template
        self.agent_type = agent_type

    def __str__(self):
        return f"'{self.name}' ({self.agent_profile_id})"

    def __repr__(self):
        return (
            f"AgentProfile("
            f"agent_generator={self.agent_generator!r}, "
            f"agent_template={self.agent_template!r}, "
            f"agent_type={self.agent_type!r}"
            f")"
        )

    @property
    def label(self) -> str:
        return self.agent_template.label

    @property
    def name(self) -> str | None:
        return self.agent_template.name

    @property
    def description(self) -> str:
        return self.agent_template.description

    @property
    def version(self) -> packaging_version.Version | None:
        return self.agent_template.version

    @property
    def compatible_framework_version(self) -> specifiers.SpecifierSet | None:
        return self.agent_template.compatible_framework_version

    @property
    def authors(self) -> set[str]:
        return self.agent_template.authors

    @property
    def component_dependencies(self) -> set[str]:
        return self.agent_template.component_dependencies

    @property
    def agent_project_folder(self) -> Path:
        return self.agent_template.agent_project_folder
