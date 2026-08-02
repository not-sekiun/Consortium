import pytest

from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateValidatingFunctionError,
)
from consortium.framework._core.framework_exceptions.listener_templates_framework_exceptions import (
    ListenerTemplateValidatingFunctionError,
)
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.framework.signal_exceptions.options_signal_exceptions import (
    OptionValueValidationError,
)


class _AgentTemplateStub:
    options = {}

    @staticmethod
    def validating_function(_parameters):
        raise OptionValueValidationError(
            message="The agent template options are incompatible.",
            detail={"reason": "incompatible"},
        )

    def __str__(self) -> str:
        return "mock-agent-template"


class _ListenerTemplateStub:
    options = {}

    @staticmethod
    def validating_function(_parameters):
        raise OptionValueValidationError(
            message="The listener template options are incompatible.",
            detail={"reason": "incompatible"},
        )

    def __str__(self) -> str:
        return "mock-listener-template"


def test_agent_template_validation_signal_is_translated():
    template = _AgentTemplateStub()

    with pytest.raises(AgentTemplateValidatingFunctionError) as exc_info:
        BaseAgentTemplate.create_agent_generator(template, parameters={})

    assert "mock-agent-template" in exc_info.value.message
    assert "agent template options are incompatible" in exc_info.value.message
    assert exc_info.value.detail == {"reason": "incompatible"}


def test_listener_template_validation_signal_is_translated():
    template = _ListenerTemplateStub()

    with pytest.raises(ListenerTemplateValidatingFunctionError) as exc_info:
        BaseListenerTemplate.create_listener(template, parameters={})

    assert "mock-listener-template" in exc_info.value.message
    assert "listener template options are incompatible" in exc_info.value.message
    assert exc_info.value.detail == {"reason": "incompatible"}
