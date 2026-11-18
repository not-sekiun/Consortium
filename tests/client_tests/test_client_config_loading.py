import json
from argparse import Namespace
from unittest.mock import AsyncMock, Mock

import pytest

import consortium.client.client as client_module
import consortium.client.start_client as start_client_module
from consortium.client.client import Client
from consortium.client.exceptions.config_exceptions import ConfigLoadError
from consortium.client.models.alias_models import Alias
from consortium.client.models.client_models import ClientConfig
from consortium.client.utils.config_utils import load_aliases_from_json_file


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def startup(tmp_path, monkeypatch):
    config_path = tmp_path / "client.json"
    config_path.write_text(
        json.dumps(
            {
                "username": "user",
                "password": "secret",
                "remote_host": "localhost",
                "remote_port": 9999,
            }
        ),
        encoding="utf-8",
    )
    logging_path = tmp_path / "logging.json"
    logging_path.write_text("{}", encoding="utf-8")
    client = Mock()
    client.run = AsyncMock()
    client_factory = Mock(return_value=client)
    logger = Mock()
    monkeypatch.setattr(start_client_module, "Client", client_factory)
    monkeypatch.setattr(start_client_module, "logger", logger)
    arguments = Namespace(
        client_config=str(config_path),
        logging_config=str(logging_path),
        debug=False,
    )
    return arguments, client_factory, logger


@pytest.mark.anyio
@pytest.mark.parametrize("config_kind", ["client", "logging"])
@pytest.mark.parametrize("contents", ["invalid JSON", "[]", "null", '"text"'])
async def test_startup_reports_invalid_config(startup, config_kind, contents, capsys):
    arguments, client_factory, logger = startup
    config_path = getattr(arguments, f"{config_kind}_config")
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(contents)

    await start_client_module._start_client(arguments)

    client_factory.assert_not_called()
    logger.remove.assert_not_called()
    output = capsys.readouterr().out
    assert f"'{config_path}'" in output
    assert "Failed to start client" in output


@pytest.mark.anyio
@pytest.mark.parametrize("invalid_fields", [{"remote_port": "9999"}, {"extra": 1}])
async def test_startup_uses_the_connection_config_contract(
    startup, invalid_fields, capsys
):
    arguments, client_factory, _ = startup
    with open(arguments.client_config, encoding="utf-8") as file:
        config = json.load(file)
    with open(arguments.client_config, "w", encoding="utf-8") as file:
        json.dump(config | invalid_fields, file)

    await start_client_module._start_client(arguments)

    client_factory.assert_not_called()
    output = capsys.readouterr().out
    assert "expected client configuration format" in output
    assert "secret" not in output


@pytest.mark.anyio
@pytest.mark.parametrize("debug", [False, True])
async def test_startup_preserves_logging_defaults_and_debug_override(startup, debug):
    arguments, client_factory, logger = startup
    arguments.debug = debug
    with open(arguments.logging_config, "w", encoding="utf-8") as file:
        json.dump({"log_file": "client.log", "level": "ERROR"}, file)

    await start_client_module._start_client(arguments)

    config = client_factory.call_args.kwargs["client_config"]
    assert config.remote_port == 9999
    client_factory.return_value.run.assert_awaited_once()
    file_logging = logger.add.call_args_list[1].kwargs
    assert file_logging["sink"] == str(
        start_client_module.CONSORTIUM_ROOT / "client.log"
    )
    assert file_logging["retention"] == 1
    assert file_logging["rotation"] is None
    assert file_logging["level"] == ("DEBUG" if debug else "ERROR")
    assert logger.add.call_args_list[0].kwargs["colorize"] is True


@pytest.fixture
def aliases_path(tmp_path, monkeypatch):
    path = tmp_path / "aliases.json"
    monkeypatch.setattr(client_module.client_config_module, "ALIASES_JSON_FILE", path)
    return path


def test_alias_config_preserves_scopes_and_global_precedence(aliases_path):
    aliases_path.write_text(
        json.dumps(
            {
                "local_aliases": {"local": "help", "shared": "local command"},
                "global_aliases": {"global": "home", "shared": "global command"},
            }
        ),
        encoding="utf-8",
    )

    aliases = load_aliases_from_json_file(path=aliases_path)

    assert aliases == {
        "local": Alias(command="help", is_global=False),
        "global": Alias(command="home", is_global=True),
        "shared": Alias(command="global command", is_global=True),
    }


@pytest.mark.parametrize(
    "contents",
    [
        "invalid JSON",
        "[]",
        "null",
        "{}",
        '{"local_aliases": {}, "global_aliases": {}, "extra": {}}',
        '{"local_aliases": {"a": 1}, "global_aliases": {}}',
        '{"local_aliases": {}, "global_aliases": {"a": false}}',
    ],
)
def test_invalid_alias_config_raises_without_printing(aliases_path, contents, capsys):
    aliases_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ConfigLoadError) as caught:
        load_aliases_from_json_file(path=aliases_path)

    assert aliases_path.name in str(caught.value)
    assert caught.value.__cause__ is not None
    assert capsys.readouterr().out == ""


def test_empty_alias_groups_are_valid(aliases_path, capsys):
    aliases_path.write_text(
        '{"local_aliases": {}, "global_aliases": {}}', encoding="utf-8"
    )

    assert load_aliases_from_json_file(path=aliases_path) == {}
    assert capsys.readouterr().out == ""


def test_client_continues_without_aliases_when_loading_fails(aliases_path, capsys):
    client = Client(
        ClientConfig(
            username="user",
            password="secret",
            remote_host="localhost",
            remote_port=9999,
        )
    )

    assert client._aliases == {}
    assert "Failed to load client aliases" in capsys.readouterr().out
