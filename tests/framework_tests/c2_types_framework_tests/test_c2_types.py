import pytest

from consortium.framework._core.framework_exceptions.c2_types_framework_exceptions import (
    AgentTypeConfigurationParameterTypeError,
    ListenerTypeConfigurationParameterTypeError,
)
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType


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


def test_invalid_agent_type_creation():
    with pytest.raises(AgentTypeConfigurationParameterTypeError):

        class _InvalidAgentType(BaseAgentType):
            name = 123


def test_invalid_listener_type_creation():
    with pytest.raises(ListenerTypeConfigurationParameterTypeError):

        class _InvalidListenerType(BaseListenerType):
            name = 123


def test_invalid_compatible_listener_types():
    with pytest.raises(AgentTypeConfigurationParameterTypeError):

        class _InvalidAgentType(BaseAgentType):
            name = 123
            compatible_listener_types = ([1, 2, 3],)


def test_invalid_compatible_agent_types():
    with pytest.raises(ListenerTypeConfigurationParameterTypeError):

        class _InvalidListenerType(BaseListenerType):
            name = 123
            compatible_agent_types = ([1, 2, 3],)
