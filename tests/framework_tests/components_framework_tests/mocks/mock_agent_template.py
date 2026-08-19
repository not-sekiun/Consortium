from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentTemplate,
    BaseAgentType,
)

from .declarations import (
    DECLARED_AUTHORS,
    DECLARED_DEPENDENCY,
    DECLARED_DESCRIPTION,
    DECLARED_FRAMEWORK_VERSION,
    DECLARED_VERSION,
    declared_options,
)
from .mock_listener_template import DECLARED_LISTENER_TYPE_NAME

DECLARED_AGENT_TYPE_NAME = "mock_metadata_agent_type"


class MockAgentGenerator(BaseAgentGenerator):
    name = "mock_metadata_agent_generator"
    description = DECLARED_DESCRIPTION
    agent_generator_build_steps = []


class MockAgentType(BaseAgentType):
    name = DECLARED_AGENT_TYPE_NAME
    agent_capabilities = set()


class MockAgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.mock_metadata"
    name = "Mock Metadata Agent Template"
    description = DECLARED_DESCRIPTION
    version = DECLARED_VERSION
    compatible_framework_version = DECLARED_FRAMEWORK_VERSION
    authors = set(DECLARED_AUTHORS)
    component_dependencies = {DECLARED_DEPENDENCY}
    agent_generator = MockAgentGenerator
    agent_type = MockAgentType
    compatible_listener_types = {DECLARED_LISTENER_TYPE_NAME}
    options = declared_options()
