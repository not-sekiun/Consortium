import json
from unittest.mock import AsyncMock, Mock

import pytest

import consortium.client.commands.home_interpreter_commands.client_session as session_module
from consortium.client.client_session import ClientSession
from consortium.client.commands.home_interpreter_commands.client_session import (
    SessionCommand,
)
from consortium.client.models.interpreter_signal_models import ContinueSignal

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def connection_details():
    return {
        "username": "file-user",
        "password": "file-password",
        "remote_host": "file-host",
        "remote_port": 9999,
    }


@pytest.fixture
def command(tmp_path, monkeypatch, connection_details):
    config_path = tmp_path / "client.json"
    config_path.write_text(json.dumps(connection_details), encoding="utf-8")
    monkeypatch.setattr(session_module, "CLIENT_CONFIG_JSON_FILE", config_path)
    command = SessionCommand()
    command._connect = AsyncMock(return_value=Mock(spec=ClientSession))
    return command


@pytest.mark.parametrize(
    ("arguments", "overrides"),
    [
        ([], {}),
        (["-u", "cli-user"], {"username": "cli-user"}),
        (["-rp", "0"], {"remote_port": 0}),
    ],
)
async def test_default_config_fills_missing_details(
    command, connection_details, arguments, overrides
):
    parsed_args = command.parse_arguments(["connect", *arguments])

    signal = await command._handle_connect_sub_command(parsed_args)

    assert isinstance(signal, ContinueSignal)
    command._connect.assert_awaited_once_with(**(connection_details | overrides))


async def test_complete_manual_details_do_not_read_a_config(command, monkeypatch):
    parsed_args = command.parse_arguments(
        [
            "connect",
            "-rh",
            "cli-host",
            "-rp",
            "1234",
            "-u",
            "cli-user",
            "-p",
            "cli-password",
        ],
    )
    monkeypatch.setattr(
        "builtins.open", Mock(side_effect=AssertionError("config read"))
    )

    await command._handle_connect_sub_command(parsed_args)

    command._connect.assert_awaited_once_with(
        remote_host="cli-host",
        remote_port=1234,
        username="cli-user",
        password="cli-password",
    )


async def test_explicit_config_is_used_with_overrides(
    command, tmp_path, connection_details
):
    config_path = tmp_path / "explicit.json"
    explicit_details = connection_details | {"remote_host": "explicit-host"}
    config_path.write_text(json.dumps(explicit_details), encoding="utf-8")
    parsed_args = command.parse_arguments(
        ["connect", "-c", str(config_path), "-u", "cli-user"],
    )

    await command._handle_connect_sub_command(parsed_args)

    command._connect.assert_awaited_once_with(
        **(explicit_details | {"username": "cli-user"}),
    )


@pytest.mark.parametrize(
    "contents", [None, "invalid JSON", '{"username": "incomplete"}']
)
async def test_explicit_invalid_config_is_reported_even_with_complete_manual_details(
    command, tmp_path, contents, capsys
):
    config_path = tmp_path / "invalid.json"
    if contents is not None:
        config_path.write_text(contents, encoding="utf-8")
    parsed_args = command.parse_arguments(
        [
            "connect",
            "-c",
            str(config_path),
            "-rh",
            "cli-host",
            "-rp",
            "1234",
            "-u",
            "cli-user",
            "-p",
            "cli-password",
        ],
    )

    signal = await command._handle_connect_sub_command(parsed_args)

    assert isinstance(signal, ContinueSignal)
    command._connect.assert_not_awaited()
    assert config_path.name in capsys.readouterr().out


async def test_explicit_empty_values_do_not_fall_back_to_config(command, capsys):
    parsed_args = command.parse_arguments(["connect", "-u", ""])

    signal = await command._handle_connect_sub_command(parsed_args)

    assert isinstance(signal, ContinueSignal)
    command._connect.assert_not_awaited()
    assert "Missing connection details: username." in capsys.readouterr().out


@pytest.mark.parametrize(
    "invalid_data",
    [
        [],
        None,
        {"remote_port": "9999"},
        {"remote_port": True},
        {"remote_port": 9999.0},
        {"remote_port": 9999.5},
        {"password": 123},
        {"unexpected": "value"},
    ],
)
async def test_invalid_connection_config_does_not_connect(
    command, tmp_path, monkeypatch, connection_details, invalid_data
):
    print_error = Mock()
    monkeypatch.setattr(session_module, "print_error", print_error)
    config_path = tmp_path / "invalid.json"
    config_data = (
        connection_details | invalid_data
        if isinstance(invalid_data, dict)
        else invalid_data
    )
    config_path.write_text(json.dumps(config_data), encoding="utf-8")
    parsed_args = command.parse_arguments(["connect", "-c", str(config_path)])

    signal = await command._handle_connect_sub_command(parsed_args)

    assert isinstance(signal, ContinueSignal)
    command._connect.assert_not_awaited()
    output = print_error.call_args.args[0]
    assert "expected client configuration" in output
    assert "file-password" not in output
