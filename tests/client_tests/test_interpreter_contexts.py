from argparse import Namespace
from collections import deque

import pytest

from consortium.client.models.alias_models import Alias
from consortium.client.models.context_models import DisconnectedContext
from consortium.client.models.interpreter_context_models import (
    BaseInterpreterContext,
    InteractAgentInterpreterContext,
    UseAgentTemplateInterpreterContext,
    UseListenerTemplateInterpreterContext,
)
from consortium.client.models.interpreter_signal_models import (
    SwitchInteractAgentInterpreterSignal,
    SwitchUseAgentTemplateInterpreterSignal,
    SwitchUseListenerTemplateInterpreterSignal,
)


@pytest.mark.parametrize(
    ("context_type", "details"),
    [
        (BaseInterpreterContext, {}),
        (UseAgentTemplateInterpreterContext, {"agent_template": {"name": "template"}}),
        (
            UseListenerTemplateInterpreterContext,
            {"listener_template": {"name": "template"}},
        ),
        (InteractAgentInterpreterContext, {"agent": {"name": "agent"}}),
    ],
)
def test_command_context_preserves_interpreter_state_references(context_type, details):
    aliases = {}
    resource_commands = deque()
    interpreter_context = context_type(
        aliases=aliases, resource_commands=resource_commands, **details
    )
    command_context = DisconnectedContext(
        command="alias",
        arguments=[],
        parsed_args=Namespace(),
        raw_input="alias load",
        interpreter_context=interpreter_context,
    )

    command_context.interpreter_context.aliases["help"] = Alias(
        command="help", is_global=False
    )
    command_context.interpreter_context.resource_commands.append("help")

    assert command_context.interpreter_context is interpreter_context
    assert interpreter_context.aliases is aliases
    assert aliases["help"].command == "help"
    assert interpreter_context.resource_commands is resource_commands
    assert list(resource_commands) == ["help"]
    for name, value in details.items():
        assert getattr(command_context.interpreter_context, name) is value


def test_default_interpreter_state_is_not_shared():
    first = BaseInterpreterContext()
    second = BaseInterpreterContext()

    first.aliases["help"] = Alias(command="help", is_global=False)
    first.resource_commands.append("help")

    assert second.aliases == {}
    assert not second.resource_commands
    assert first.commands_info is not second.commands_info


@pytest.mark.parametrize(
    ("signal_type", "context_type", "field_name"),
    [
        (
            SwitchUseAgentTemplateInterpreterSignal,
            UseAgentTemplateInterpreterContext,
            "agent_template",
        ),
        (
            SwitchUseListenerTemplateInterpreterSignal,
            UseListenerTemplateInterpreterContext,
            "listener_template",
        ),
        (
            SwitchInteractAgentInterpreterSignal,
            InteractAgentInterpreterContext,
            "agent",
        ),
    ],
)
def test_interpreter_switch_preserves_resource_reference(
    signal_type, context_type, field_name
):
    resource = {"name": "original"}
    signal = signal_type(**{field_name: resource})
    interpreter_context = context_type(**{field_name: getattr(signal, field_name)})
    command_context = DisconnectedContext(
        command="help",
        arguments=[],
        parsed_args=Namespace(),
        raw_input="help",
        interpreter_context=interpreter_context,
    )

    resource["name"] = "updated"

    assert getattr(signal, field_name) is resource
    assert command_context.interpreter_context is interpreter_context
    assert getattr(command_context.interpreter_context, field_name) is resource
    assert getattr(command_context.interpreter_context, field_name)["name"] == "updated"
