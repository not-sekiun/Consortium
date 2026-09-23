from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentTemplate,
    BaseAgentType,
)
from consortium.framework.listeners import (
    BaseListener,
    BaseListenerTemplate,
    BaseListenerType,
)

# Regression for the per-instance template binding fix: two templates that share one
# generator (or listener) class used to overwrite each other's binding at the class
# level, so every instance reported the last-loaded template's type. Each instance must
# now report its own creating template and the type derived from it.


class _AgentTypeA(BaseAgentType):
    name = "type_a"
    agent_capabilities = set()


class _AgentTypeB(BaseAgentType):
    name = "type_b"
    agent_capabilities = set()


class _SharedAgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = []


class _AgentTemplateA(BaseAgentTemplate):
    label = "consortium.agents.binding_a"
    name = "Binding Agent A"
    description = "Shares a generator class with template B."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    agent_generator = _SharedAgentGenerator
    agent_type = _AgentTypeA
    compatible_listener_types = {"listener_a"}
    options = set()


class _AgentTemplateB(BaseAgentTemplate):
    label = "consortium.agents.binding_b"
    name = "Binding Agent B"
    description = "Shares a generator class with template A."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    agent_generator = _SharedAgentGenerator
    agent_type = _AgentTypeB
    compatible_listener_types = {"listener_b"}
    options = set()


def test_shared_agent_generator_class_binds_per_instance():
    template_a = _AgentTemplateA()
    template_b = _AgentTemplateB()

    generator_a = template_a.create_agent_generator()
    generator_b = template_b.create_agent_generator()

    # Each instance reports its own creating template, not the last one bound.
    assert generator_a.creating_agent_template is template_a
    assert generator_b.creating_agent_template is template_b

    assert generator_a.agent_type is _AgentTypeA
    assert generator_b.agent_type is _AgentTypeB

    assert generator_a.compatible_listener_types == {"listener_a"}
    assert generator_b.compatible_listener_types == {"listener_b"}


class _ListenerTypeA(BaseListenerType):
    name = "listener_type_a"


class _ListenerTypeB(BaseListenerType):
    name = "listener_type_b"


class _SharedListener(BaseListener):
    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...


class _ListenerTemplateA(BaseListenerTemplate):
    label = "consortium.listeners.binding_a"
    name = "Binding Listener A"
    description = "Shares a listener class with template B."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    listener = _SharedListener
    listener_type = _ListenerTypeA
    options = set()

    def resolve_listener_endpoint(self, parameters) -> str:
        return ""


class _ListenerTemplateB(BaseListenerTemplate):
    label = "consortium.listeners.binding_b"
    name = "Binding Listener B"
    description = "Shares a listener class with template A."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    listener = _SharedListener
    listener_type = _ListenerTypeB
    options = set()

    def resolve_listener_endpoint(self, parameters) -> str:
        return ""


def test_shared_listener_class_binds_per_instance():
    template_a = _ListenerTemplateA()
    template_b = _ListenerTemplateB()

    listener_a = template_a.create_listener()
    listener_b = template_b.create_listener()

    assert listener_a.creating_listener_template is template_a
    assert listener_b.creating_listener_template is template_b

    assert listener_a.listener_type is _ListenerTypeA
    assert listener_b.listener_type is _ListenerTypeB
