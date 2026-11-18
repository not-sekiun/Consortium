from argparse import ArgumentParser
from unittest.mock import AsyncMock, Mock

import pytest

from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.exec import ExecCommand
from consortium.client.commands.generators_interpreter_commands.generator_update import (
    GeneratorUpdateCommand,
)
from consortium.client.commands.home_interpreter_commands.client_session import (
    SessionCommand,
)
from consortium.client.commands.interact_agent_interpreter_commands.agent_capability_command import (
    construct_agent_capability_command,
)
from consortium.client.commands.listeners_interpreter_commands.listener_update import (
    ListenerUpdateCommand,
)
from consortium.client.commands.use_agent_template_interpreter_commands.agent_template_set_option import (
    AgentTemplateSetOptionCommand,
)
from consortium.client.commands.use_listener_template_interpreter_commands.listener_template_set_option import (
    ListenerTemplateSetOptionCommand,
)
from consortium.client.models.context_models import (
    AnyContext,
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchHomeInterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.repl_interface.base_interpreter import _BaseInterpreter
from consortium.client.repl_interface.parser import ParsedCommand

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


class _InspectCommand(BaseCommand[AnyContext]):
    name = "inspect"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("value", type=int)

    async def run(self, context: AnyContext) -> InterpreterSignal:
        return SwitchHomeInterpreterSignal()


def _interpreter(command: BaseCommand, connected: bool = False) -> _BaseInterpreter:
    # Dispatch needs no prompt session or live server connection.
    interpreter = object.__new__(_BaseInterpreter)
    interpreter.commands = {command.name: command}
    interpreter.client_session = object.__new__(ClientSession) if connected else None
    interpreter.interpreter_context = BaseInterpreterContext()
    return interpreter


def _input(command: str, arguments: list[str]) -> ParsedCommand:
    return ParsedCommand(
        command=command,
        arguments=arguments,
        raw_input=" ".join([command, *arguments]),
    )


@pytest.mark.parametrize("connected", [False, True])
async def test_dispatch_parses_once_and_supplies_the_execution_context(connected):
    command = _InspectCommand()
    command.parse_arguments = Mock(wraps=command.parse_arguments)
    command.run = AsyncMock(wraps=command.run)
    interpreter = _interpreter(command, connected=connected)
    parsed_command = _input(command.name, ["42"])

    signal = await interpreter._dispatch_command(parsed_command)

    command.parse_arguments.assert_called_once_with(["42"])
    command.run.assert_awaited_once()
    context = command.run.call_args.kwargs["context"]
    assert isinstance(context, ConnectedContext if connected else DisconnectedContext)
    assert context.command == command.name
    assert context.arguments == ["42"]
    assert context.raw_input == parsed_command.raw_input
    assert context.parsed_args.value == 42
    assert context.interpreter_context is interpreter.interpreter_context
    if connected:
        assert context.client_session is interpreter.client_session
    assert isinstance(signal, SwitchHomeInterpreterSignal)


@pytest.mark.parametrize(
    ("arguments", "output"),
    [
        (["--help"], "usage:"),
        ([], "required"),
        (["invalid"], "invalid int value"),
        (["42", "--unknown"], "unrecognized arguments"),
    ],
)
async def test_dispatch_returns_to_the_prompt_without_executing(arguments, output, capsys):
    command = _InspectCommand()
    command.run = AsyncMock()
    interpreter = _interpreter(command)

    signal = await interpreter._dispatch_command(_input(command.name, arguments))

    assert isinstance(signal, ContinueSignal)
    command.run.assert_not_awaited()
    captured = capsys.readouterr()
    assert output in captured.out + captured.err


async def test_dispatch_does_not_swallow_an_exit_from_execution():
    command = _InspectCommand()
    command.run = AsyncMock(side_effect=SystemExit(7))
    interpreter = _interpreter(command)

    with pytest.raises(SystemExit) as raised:
        await interpreter._dispatch_command(_input(command.name, ["42"]))

    assert raised.value.code == 7


@pytest.mark.parametrize(
    ("command_factory", "arguments", "error"),
    [
        (ExecCommand, [], "shell_command"),
        (SessionCommand, ["connect", "-c"], "expected one argument"),
        (SessionCommand, ["connect", "-c", "-u", "operator"], "expected one argument"),
    ],
)
async def test_dispatch_runs_custom_argument_validation(
    command_factory, arguments, error, capsys
):
    command = command_factory()
    command.run = AsyncMock()
    interpreter = _interpreter(command)

    signal = await interpreter._dispatch_command(_input(command.name, arguments))

    assert isinstance(signal, ContinueSignal)
    command.run.assert_not_awaited()
    assert error in capsys.readouterr().err


@pytest.mark.parametrize(
    "command_factory",
    [
        GeneratorUpdateCommand,
        ListenerUpdateCommand,
        AgentTemplateSetOptionCommand,
        ListenerTemplateSetOptionCommand,
        lambda: construct_agent_capability_command(
            {"name": "inspect", "description": "Inspect an agent", "options": {}},
        ),
    ],
)
async def test_full_help_needs_no_required_arguments_and_restores_epilog(
    command_factory, capsys
):
    command = command_factory()
    original_epilog = command.parser.epilog
    command.run = AsyncMock()
    interpreter = _interpreter(command)

    signal = await interpreter._dispatch_command(_input(command.name, ["--help-full"]))

    assert isinstance(signal, ContinueSignal)
    command.run.assert_not_awaited()
    assert command.parser.epilog == original_epilog
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "Examples:" in captured.out
    assert not captured.err
