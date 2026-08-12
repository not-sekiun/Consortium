import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import consortium.server.server_singletons as _ss
from consortium.framework.agents.agent_message_models import (
    RegistrationMessageModel,
    TaskOutputMessageModel,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
)
from consortium.server.services.connected_agents_service import ConnectedAgentsService


@pytest.fixture
def listener_id():
    return uuid.uuid4()


@pytest.fixture
def mock_agents_service():
    return MagicMock()


@pytest.fixture
def service(listener_id, mock_agents_service):
    with patch.object(_ss, "agents_service", mock_agents_service):
        svc = ConnectedAgentsService(listener_id=listener_id)
    return svc


def _make_connected_agent(listener_id):
    agent = MagicMock()
    agent.agent_id = uuid.uuid4()
    agent.connected_listener = MagicMock()
    agent.connected_listener.listener_id = listener_id
    return agent


def _make_disconnected_agent():
    agent = MagicMock()
    agent.agent_id = uuid.uuid4()
    agent.connected_listener = None
    return agent


def _make_wrong_listener_agent():
    agent = MagicMock()
    agent.agent_id = uuid.uuid4()
    agent.connected_listener = MagicMock()
    agent.connected_listener.listener_id = uuid.uuid4()
    return agent


# --- __str__ / __repr__ ---


def test_str(service):
    assert str(service) == "Connected Agents Service"


def test_repr(service):
    assert repr(service) == "ConnectedAgentsService()"


# --- _validate_agent_connected_to_listener ---


def test_validate_connected_agent_succeeds(service, mock_agents_service, listener_id):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    result = service._validate_agent_connected_to_listener(agent_id=agent.agent_id)
    assert result == agent


def test_validate_disconnected_agent_raises(service, mock_agents_service):
    agent = _make_disconnected_agent()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    with pytest.raises(AgentNotFoundError):
        service._validate_agent_connected_to_listener(agent_id=agent.agent_id)


def test_validate_wrong_listener_raises(service, mock_agents_service):
    agent = _make_wrong_listener_agent()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    with pytest.raises(AgentNotFoundError):
        service._validate_agent_connected_to_listener(agent_id=agent.agent_id)


# --- register_agent ---


def test_register_agent_delegates(service, mock_agents_service, listener_id):
    expected = MagicMock()
    registration = RegistrationMessageModel(
        agent_type="mock_alpha", endpoint="127.0.0.1"
    )
    mock_agents_service.register_agent.return_value = expected
    result = service.register_agent(registration_message=registration, name="agent1")
    mock_agents_service.register_agent.assert_called_once_with(
        listener_id=listener_id,
        registration_message=registration,
        payload_id=None,
        agent_type=None,
        name="agent1",
        description="",
        endpoint="",
        user=None,
        is_admin=None,
        os=None,
        version=None,
        arch=None,
        pid=None,
        locale=None,
        remote_ip=None,
        local_ip=None,
        hostname=None,
        agent_data=None,
    )
    assert result == expected


def test_register_agent_delegates_individual_fields(
    service, mock_agents_service, listener_id
):
    expected = MagicMock()
    mock_agents_service.register_agent.return_value = expected
    result = service.register_agent(
        agent_type="mock_alpha",
        endpoint="127.0.0.1",
        hostname="host-1",
        name="agent1",
    )
    call_kwargs = mock_agents_service.register_agent.call_args.kwargs
    assert call_kwargs["registration_message"] is None
    assert call_kwargs["agent_type"] == "mock_alpha"
    assert call_kwargs["endpoint"] == "127.0.0.1"
    assert call_kwargs["hostname"] == "host-1"
    assert result == expected


# --- deregister_agent_by_agent_id ---


def test_deregister_agent_validates_then_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    service.deregister_agent_by_agent_id(agent_id=agent.agent_id)
    mock_agents_service.deregister_agent_by_agent_id.assert_called_once_with(
        agent_id=agent.agent_id
    )


def test_deregister_wrong_listener_raises(service, mock_agents_service):
    agent = _make_wrong_listener_agent()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    with pytest.raises(AgentNotFoundError):
        service.deregister_agent_by_agent_id(agent_id=agent.agent_id)


# --- check_in_agent_by_agent_id ---


def test_check_in_agent_validates_then_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    service.check_in_agent_by_agent_id(agent_id=agent.agent_id)
    mock_agents_service.check_in_agent_by_agent_id.assert_called_once_with(
        agent_id=agent.agent_id
    )


# --- get_next_task_message_by_task_id ---


@pytest.mark.anyio
async def test_get_next_task_message_by_task_id_validates_and_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    task_id = uuid.uuid4()
    expected = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.get_next_task_message_by_task_id = AsyncMock(
        return_value=expected
    )
    result = await service.get_next_task_message_by_task_id(
        agent_id=agent.agent_id, task_id=task_id, timeout=1.0
    )
    mock_agents_service.get_next_task_message_by_task_id.assert_called_once_with(
        agent_id=agent.agent_id, task_id=task_id, timeout=1.0
    )
    assert result == expected


@pytest.mark.anyio
async def test_get_next_task_message_by_task_id_wrong_listener_raises(
    service, mock_agents_service
):
    agent = _make_wrong_listener_agent()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.get_next_task_message_by_task_id = AsyncMock()
    with pytest.raises(AgentNotFoundError):
        await service.get_next_task_message_by_task_id(
            agent_id=agent.agent_id, task_id=uuid.uuid4()
        )
    mock_agents_service.get_next_task_message_by_task_id.assert_not_called()


# --- get_next_task_message_sequential ---


@pytest.mark.anyio
async def test_get_next_task_message_sequential_validates_and_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    expected = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.get_next_task_message_sequential = AsyncMock(
        return_value=expected
    )
    result = await service.get_next_task_message_sequential(
        agent_id=agent.agent_id, timeout=None
    )
    mock_agents_service.get_next_task_message_sequential.assert_called_once_with(
        agent_id=agent.agent_id, timeout=None
    )
    assert result == expected


# --- get_next_task_message_any ---


@pytest.mark.anyio
async def test_get_next_task_message_any_validates_and_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    expected = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.get_next_task_message_any = AsyncMock(return_value=expected)
    result = await service.get_next_task_message_any(agent_id=agent.agent_id, timeout=0)
    mock_agents_service.get_next_task_message_any.assert_called_once_with(
        agent_id=agent.agent_id, timeout=0
    )
    assert result == expected


# --- dispatch_task_output_message ---


@pytest.mark.anyio
async def test_dispatch_task_output_message_validates_and_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    task_id = uuid.uuid4()
    output = TaskOutputMessageModel(
        task_id=task_id,
        success=True,
        message="done",
        data={"key": "val"},
    )
    agent.get_running_task_by_task_id.return_value = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.dispatch_task_output_message = AsyncMock()

    await service.dispatch_task_output_message(
        agent_id=agent.agent_id,
        task_output_message=output,
    )
    agent.get_running_task_by_task_id.assert_called_once_with(task_id=task_id)
    mock_agents_service.check_in_agent_by_agent_id.assert_called_with(
        agent_id=agent.agent_id
    )
    mock_agents_service.dispatch_task_output_message.assert_called_once_with(
        agent_id=agent.agent_id,
        task_output_message=output,
    )


@pytest.mark.anyio
async def test_dispatch_task_output_message_assembles_individual_fields(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    task_id = uuid.uuid4()
    agent.get_running_task_by_task_id.return_value = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.dispatch_task_output_message = AsyncMock()

    await service.dispatch_task_output_message(
        agent_id=agent.agent_id,
        task_id=task_id,
        success=True,
        message="done",
        data={"key": "val"},
    )
    # The running-task check must see the assembled task ID, not skip it.
    agent.get_running_task_by_task_id.assert_called_once_with(task_id=task_id)
    assembled = mock_agents_service.dispatch_task_output_message.call_args.kwargs[
        "task_output_message"
    ]
    assert assembled.task_id == task_id
    assert assembled.success is True
    assert assembled.message == "done"
    assert assembled.data == {"key": "val"}


@pytest.mark.anyio
async def test_dispatch_task_output_message_requires_a_message_or_fields(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.dispatch_task_output_message = AsyncMock()

    with pytest.raises(ValueError):
        await service.dispatch_task_output_message(agent_id=agent.agent_id)


# --- get_all_agents ---


def test_get_all_agents_filters_by_listener(service, mock_agents_service, listener_id):
    agent_mine = _make_connected_agent(listener_id)
    agent_other = _make_wrong_listener_agent()
    agent_no_listener = _make_disconnected_agent()
    mock_agents_service.get_all_agents.return_value = [
        agent_mine,
        agent_other,
        agent_no_listener,
    ]

    result = service.get_all_agents()
    assert agent_mine in result
    assert agent_other not in result
    assert agent_no_listener not in result


# --- get_agent_by_agent_id ---


def test_get_agent_by_agent_id_returns_validated(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    result = service.get_agent_by_agent_id(agent_id=agent.agent_id)
    assert result == agent


def test_get_agent_by_agent_id_wrong_listener_raises(service, mock_agents_service):
    agent = _make_wrong_listener_agent()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    with pytest.raises(AgentNotFoundError):
        service.get_agent_by_agent_id(agent_id=agent.agent_id)
