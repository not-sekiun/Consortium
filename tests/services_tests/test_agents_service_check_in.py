from unittest.mock import AsyncMock, MagicMock

import pytest

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.services.agents_service import AgentsService

pytestmark = pytest.mark.anyio

# The AGENT_CHECKED_IN payload used to be serialized while the coroutine arguments were
# built, which happened before the check-in timestamp and status were written. Anything
# driven off the event stream therefore lagged a check-in behind. The agent is updated
# first now, so the emitted payload describes this check-in.


@pytest.fixture
def service():
    return AgentsService(
        events_service=MagicMock(trigger_event=AsyncMock()),
        tasks_service=MagicMock(),
        task_runtime_service=MagicMock(),
    )


def _agent_stub() -> MagicMock:
    agent = MagicMock()
    agent.datetime_last_checked_in = "stale"
    # to_json reads through to the live attribute, so the captured payload shows
    # whichever value was set at the moment it was called.
    agent.to_json.side_effect = lambda: {
        "datetime_last_checked_in": agent.datetime_last_checked_in
    }
    return agent


async def test_check_in_emits_the_updated_timestamp(service):
    agent = _agent_stub()
    service.get_agent_by_agent_id = MagicMock(return_value=agent)

    service.check_in_agent_by_agent_id(agent_id="any-id")

    service._events_service.trigger_event.assert_called_once()
    emitted = service._events_service.trigger_event.call_args.kwargs
    assert emitted["event_type"] is EventType.AGENT_CHECKED_IN
    assert emitted["data"]["datetime_last_checked_in"] != "stale"
    assert emitted["data"]["datetime_last_checked_in"] == (
        agent.datetime_last_checked_in
    )


async def test_check_in_marks_the_agent_active_before_serializing(service):
    agent = _agent_stub()
    service.get_agent_by_agent_id = MagicMock(return_value=agent)

    service.check_in_agent_by_agent_id(agent_id="any-id")

    agent.mark_as_active.assert_called_once()
    # mark_as_active has to land before the payload is built, not after.
    call_order = [call[0] for call in agent.mock_calls]
    assert call_order.index("mark_as_active") < call_order.index("to_json")
