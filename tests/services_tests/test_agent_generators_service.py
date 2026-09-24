import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from consortium.server.exceptions.service_exceptions.agent_generators_service_exceptions import (
    AgentGeneratorAlreadyExistsError,
)
from consortium.server.services.agent_generators_service import AgentGeneratorsService

pytestmark = pytest.mark.anyio

# `create` used to write into the registry unconditionally while `add` guarded against a
# duplicate ID, so the two registration paths enforced different invariants: a colliding
# ID silently replaced a live generator instead of being rejected.


@pytest.fixture
def service():
    return AgentGeneratorsService(
        agent_templates_service=MagicMock(),
        events_service=MagicMock(trigger_event=AsyncMock()),
    )


def _generator_with_id(agent_generator_id: uuid.UUID) -> MagicMock:
    generator = MagicMock()
    generator.agent_generator_id = agent_generator_id
    return generator


async def test_create_rejects_a_colliding_generator_id(service):
    colliding_id = uuid.uuid4()
    existing = _generator_with_id(colliding_id)
    service._agent_generators[str(colliding_id)] = existing

    template = MagicMock()
    template.create_agent_generator.return_value = _generator_with_id(colliding_id)
    service._agent_templates_service.get_agent_template_by_agent_template_id.return_value = template

    with pytest.raises(AgentGeneratorAlreadyExistsError):
        service.create_agent_generator_from_agent_template_by_agent_template_id(
            agent_template_id=uuid.uuid4(),
            parameters={},
        )

    # The live generator is still the one registered, not the colliding newcomer.
    assert service._agent_generators[str(colliding_id)] is existing


async def test_create_registers_a_fresh_generator(service):
    generator = _generator_with_id(uuid.uuid4())
    template = MagicMock()
    template.create_agent_generator.return_value = generator
    service._agent_templates_service.get_agent_template_by_agent_template_id.return_value = template

    created = service.create_agent_generator_from_agent_template_by_agent_template_id(
        agent_template_id=uuid.uuid4(),
        parameters={},
    )

    assert created is generator
    assert service._agent_generators[str(generator.agent_generator_id)] is generator
