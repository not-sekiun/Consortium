from unittest.mock import AsyncMock, MagicMock

import pytest

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
from consortium.framework.options import SingleValueOption
from consortium.server.services.agent_generators_service import AgentGeneratorsService
from consortium.server.services.listeners_service import ListenersService

# Both update methods back-fill the parameters the caller left out. They used to write
# those back into the caller's dict, silently expanding a partial update into the full
# resolved set (and handing the caller values, possibly secret, it never supplied).
# The resolution now happens in a local copy.


def _options() -> set[SingleValueOption]:
    return {
        SingleValueOption(
            name="host",
            description="Callback host.",
            required=False,
            value_type=str,
            validating_regex=r"^.+$",
            default_value="127.0.0.1",
        ),
        SingleValueOption(
            name="secret",
            description="Shared key.",
            required=False,
            value_type=str,
            validating_regex=r"^.+$",
            default_value="original-secret",
        ),
    }


class _AgentType(BaseAgentType):
    name = "mutation_agent_type"
    agent_capabilities = set()


class _Generator(BaseAgentGenerator):
    agent_generator_build_steps = []


class _AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.mutation"
    name = "Mutation Agent"
    description = "Template used to check the caller's dict is left alone."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    agent_generator = _Generator
    agent_type = _AgentType
    compatible_listener_types = set()
    options = _options()


class _ListenerType(BaseListenerType):
    name = "mutation_listener_type"


class _Listener(BaseListener):
    pass


class _ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.mutation"
    name = "Mutation Listener"
    description = "Template used to check the caller's dict is left alone."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"test"}
    listener = _Listener
    listener_type = _ListenerType
    compatible_agent_types = set()
    options = _options()

    def resolve_listener_endpoint(self, parameters) -> str:
        return f"http://{parameters['host']}/check-in"


@pytest.mark.anyio
async def test_updating_a_generator_leaves_the_caller_parameters_alone():
    template = _AgentTemplate()
    # The profile loader instantiates the declared type onto the loaded template, which
    # is the shape the generator's to_json() expects.
    template.agent_type = _AgentType()
    generator = template.create_agent_generator(parameters={"host": "127.0.0.1"})

    service = AgentGeneratorsService(
        agent_templates_service=MagicMock(),
        events_service=MagicMock(trigger_event=AsyncMock()),
    )
    service._agent_generators[str(generator.agent_generator_id)] = generator

    caller_parameters = {"host": "10.0.0.1"}
    service.update_agent_generator_by_agent_generator_id(
        agent_generator_id=generator.agent_generator_id,
        parameters=caller_parameters,
    )

    # Only the key the caller passed is still present: `secret` was resolved locally.
    assert caller_parameters == {"host": "10.0.0.1"}
    assert generator.parameters["host"] == "10.0.0.1"
    assert generator.parameters["secret"] == "original-secret"


@pytest.mark.anyio
async def test_updating_a_listener_leaves_the_caller_parameters_alone():
    template = _ListenerTemplate()
    template.listener_type = _ListenerType()
    listener = template.create_listener(parameters={"host": "127.0.0.1"})

    service = ListenersService(
        listener_templates_service=MagicMock(),
        events_service=MagicMock(trigger_event=AsyncMock()),
    )
    service._listeners[str(listener.listener_id)] = listener

    caller_parameters = {"host": "10.0.0.1"}
    service.update_listener_by_listener_id(
        listener_id=listener.listener_id,
        parameters=caller_parameters,
    )

    assert caller_parameters == {"host": "10.0.0.1"}
    assert listener.parameters["host"] == "10.0.0.1"
    assert listener.parameters["secret"] == "original-secret"
