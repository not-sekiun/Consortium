import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import consortium.server.server_singletons as _ss
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
    mock_agents_service.register_agent.return_value = expected
    result = service.register_agent(name="agent1", endpoint="127.0.0.1")
    mock_agents_service.register_agent.assert_called_once_with(
        listener_id=listener_id,
        payload_id=None,
        agent_type=None,
        name="agent1",
        description="",
        endpoint="127.0.0.1",
        user=None,
        is_admin=None,
        os=None,
        version=None,
        arch=None,
        pid=None,
        locale=None,
        remote_host_address=None,
        local_host_address=None,
        hostname=None,
        agent_data=None,
    )
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


# --- get_next_agent_task_messages_by_agent_id ---


@pytest.mark.anyio
async def test_get_next_task_messages_validates_checks_in_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.get_next_agent_task_messages_by_agent_id = AsyncMock(
        return_value=[]
    )
    result = await service.get_next_agent_task_messages_by_agent_id(
        agent_id=agent.agent_id, count=1
    )
    mock_agents_service.check_in_agent_by_agent_id.assert_called_with(
        agent_id=agent.agent_id
    )
    mock_agents_service.get_next_agent_task_messages_by_agent_id.assert_called_once_with(
        agent_id=agent.agent_id, count=1, block=False, timeout=None
    )
    assert result == []


# --- submit_result_by_agent_id ---


@pytest.mark.anyio
async def test_submit_result_validates_and_delegates(
    service, mock_agents_service, listener_id
):
    agent = _make_connected_agent(listener_id)
    task_id = uuid.uuid4()
    agent.get_running_task_by_task_id.return_value = MagicMock()
    mock_agents_service.get_agent_by_agent_id.return_value = agent
    mock_agents_service.submit_result_by_agent_id = AsyncMock()

    await service.submit_result_by_agent_id(
        agent_id=agent.agent_id,
        task_id=task_id,
        success=True,
        message="done",
        data={"key": "val"},
    )
    agent.get_running_task_by_task_id.assert_called_once_with(task_id=task_id)
    mock_agents_service.check_in_agent_by_agent_id.assert_called_with(
        agent_id=agent.agent_id
    )
    mock_agents_service.submit_result_by_agent_id.assert_called_once()


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
