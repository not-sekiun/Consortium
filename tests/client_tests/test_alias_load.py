import json

import pytest

import consortium.client.commands.core_commands.alias as alias_module
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.alias import AliasCommand
from consortium.client.models.alias_models import Alias
from consortium.client.models.context_models import (
    ConnectedContext,
    DisconnectedContext,
)
from consortium.client.models.interpreter_context_models import BaseInterpreterContext
from consortium.client.models.interpreter_signal_models import ContinueSignal

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def alias_file(tmp_path, monkeypatch):
    path = tmp_path / "aliases.json"
    path.write_text(
        json.dumps({"local_aliases": {"loaded": "help"}, "global_aliases": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(alias_module.client_config, "ALIASES_JSON_FILE", path)
    return path


@pytest.fixture(params=[False, True], ids=["disconnected", "connected"])
def context_factory(request):
    def create(parsed_args, aliases):
        values = {
            "command": "alias",
            "arguments": [],
            "parsed_args": parsed_args,
            "raw_input": "alias load",
            "interpreter_context": BaseInterpreterContext(aliases=aliases),
        }
        if request.param:
            return ConnectedContext(
                **values, client_session=object.__new__(ClientSession)
            )
        return DisconnectedContext(**values)

    return create


async def test_alias_load_reloads_default_and_preserves_shared_mapping(
    alias_file, context_factory
):
    command = AliasCommand()
    aliases = {"old": Alias(command="home", is_global=False)}
    other_interpreter = BaseInterpreterContext(aliases=aliases)
    context = context_factory(command.parse_arguments(["load"]), aliases)

    signal = await command.run(context)

    assert isinstance(signal, ContinueSignal)
    assert context.interpreter_context.aliases is aliases
    assert other_interpreter.aliases is aliases
    assert aliases == {"loaded": Alias(command="help", is_global=False)}
    next_interpreter = BaseInterpreterContext(aliases=aliases)
    assert next_interpreter.aliases == aliases


async def test_alias_load_custom_file_does_not_write_default(
    alias_file, tmp_path, context_factory
):
    default_contents = alias_file.read_bytes()
    custom_file = tmp_path / "custom aliases.json"
    custom_file.write_text(
        '{"local_aliases": {}, "global_aliases": {"custom": "home"}}',
        encoding="utf-8",
    )
    command = AliasCommand()
    aliases = {}
    context = context_factory(
        command.parse_arguments(["load", str(custom_file)]), aliases
    )

    await command.run(context)

    assert aliases == {"custom": Alias(command="home", is_global=True)}
    assert alias_file.read_bytes() == default_contents


@pytest.mark.parametrize("contents", [None, "invalid JSON", "[]", "{}"])
async def test_failed_alias_load_preserves_existing_aliases(
    alias_file, tmp_path, context_factory, contents, capsys
):
    invalid_file = tmp_path / "invalid.json"
    if contents is not None:
        invalid_file.write_text(contents, encoding="utf-8")
    command = AliasCommand()
    aliases = {"old": Alias(command="help", is_global=False)}
    context = context_factory(
        command.parse_arguments(["load", str(invalid_file)]), aliases
    )

    signal = await command.run(context)

    assert isinstance(signal, ContinueSignal)
    assert aliases == {"old": Alias(command="help", is_global=False)}
    output = capsys.readouterr().out
    assert invalid_file.name in output
    assert "Loaded" not in output


async def test_alias_load_empty_config_clears_aliases(alias_file, context_factory):
    alias_file.write_text(
        '{"local_aliases": {}, "global_aliases": {}}', encoding="utf-8"
    )
    command = AliasCommand()
    aliases = {"old": Alias(command="help", is_global=False)}
    context = context_factory(command.parse_arguments(["load"]), aliases)

    await command.run(context)

    assert aliases == {}
