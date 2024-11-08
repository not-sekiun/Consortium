import pytest

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeAlreadyExistsError,
    AgentTypeConfigurationError,
    AgentTypeConfigurationParameterTypeError,
    AgentTypeNotFoundError,
    ListenerTypeAlreadyExistsError,
    ListenerTypeConfigurationError,
    ListenerTypeConfigurationParameterTypeError,
    ListenerTypeNotFoundError,
)


class _TestBaseAgentType(BaseAgentType):
    name = "Test Base Agent Type"


class _TestBaseListenerType(BaseListenerType):
    name = "Test Base Listener Type"


@pytest.fixture
def agent_type():
    return _TestBaseAgentType()


@pytest.fixture
def listener_type():
    return _TestBaseListenerType()


def test_agent_type_creation(agent_type):
    assert agent_type.name == "Test Base Agent Type"


def test_listener_type_creation(listener_type):
    assert listener_type.name == "Test Base Listener Type"


def test_add_compatible_listener_type(agent_type, listener_type):
    agent_type.add_compatible_listener_type(listener_type)
    assert listener_type in agent_type.compatible_listener_types


def test_add_compatible_listener_type_invalid(agent_type):
    with pytest.raises(AgentTypeConfigurationParameterTypeError):
        agent_type.add_compatible_listener_type("InvalidListenerType")


def test_remove_compatible_listener_type(agent_type, listener_type):
    agent_type.add_compatible_listener_type(listener_type)
    agent_type.remove_compatible_listener_type(listener_type)
    assert listener_type not in agent_type.compatible_listener_types


def test_remove_compatible_listener_type_not_found(agent_type, listener_type):
    with pytest.raises(ListenerTypeNotFoundError):
        agent_type.remove_compatible_listener_type(listener_type)


def test_add_compatible_agent_type(listener_type, agent_type):
    listener_type.add_compatible_agent_type(agent_type)
    assert agent_type in listener_type.compatible_agent_types


def test_add_compatible_agent_type_invalid(listener_type):
    with pytest.raises(ListenerTypeConfigurationParameterTypeError):
        listener_type.add_compatible_agent_type("InvalidAgentType")


def test_remove_compatible_agent_type(listener_type, agent_type):
    listener_type.add_compatible_agent_type(agent_type)
    listener_type.remove_compatible_agent_type(agent_type)
    assert agent_type not in listener_type.compatible_agent_types


def test_remove_compatible_agent_type_not_found(listener_type, agent_type):
    with pytest.raises(AgentTypeNotFoundError):
        listener_type.remove_compatible_agent_type(agent_type)


def test_invalid_agent_type_creation():
    with pytest.raises(AgentTypeConfigurationError):

        class _InvalidAgentType(BaseAgentType):
            name = 123


def test_invalid_listener_type_creation():
    with pytest.raises(ListenerTypeConfigurationError):

        class _InvalidListenerType(BaseListenerType):
            name = 123


def test_invalid_compatible_listener_types():
    with pytest.raises(AgentTypeConfigurationError):

        class _InvalidAgentType(BaseAgentType):
            name = 123
            compatible_listener_types = ([1, 2, 3],)


def test_invalid_compatible_agent_types():
    with pytest.raises(ListenerTypeConfigurationError):

        class _InvalidListenerType(BaseListenerType):
            name = 123
            compatible_agent_types = ([1, 2, 3],)


def test_add_existing_compatible_listener_type(agent_type, listener_type):
    agent_type.add_compatible_listener_type(listener_type)
    with pytest.raises(ListenerTypeAlreadyExistsError):
        agent_type.add_compatible_listener_type(listener_type)


def test_add_existing_compatible_agent_type(listener_type, agent_type):
    listener_type.add_compatible_agent_type(agent_type)
    with pytest.raises(AgentTypeAlreadyExistsError):
        listener_type.add_compatible_agent_type(agent_type)
