import json
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from consortium.client.exceptions.config_exceptions import ConfigLoadError
from consortium.client.models.alias_models import AliasesConfig
from consortium.client.utils.config_utils import load_config_model_from_json_file


@pytest.mark.parametrize("as_string", [False, True])
def test_load_json_model_returns_a_validated_model(tmp_path, as_string, capsys):
    path = tmp_path / "aliases.json"
    path.write_text(
        '{"local_aliases": {"a": "help"}, "global_aliases": {}}', encoding="utf-8"
    )

    config = load_config_model_from_json_file(
        path=str(path) if as_string else path,
        model=AliasesConfig,
        description="alias configuration",
    )

    assert isinstance(config, AliasesConfig)
    assert config.local_aliases == {"a": "help"}
    assert config.global_aliases == {}
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError("missing"), "Could not find"),
        (IsADirectoryError("directory"), "is a directory"),
        (PermissionError("denied"), "Permission denied"),
        (OSError("read failed"), "Could not read"),
    ],
)
def test_load_json_model_wraps_filesystem_errors(monkeypatch, error, message, capsys):
    monkeypatch.setattr("builtins.open", Mock(side_effect=error))

    with pytest.raises(ConfigLoadError) as caught:
        load_config_model_from_json_file(
            path="aliases.json",
            model=AliasesConfig,
            description="alias configuration",
        )

    assert message in str(caught.value)
    assert "alias configuration" in str(caught.value)
    assert "aliases.json" in str(caught.value)
    assert caught.value.__cause__ is error
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("contents", "cause_type", "message"),
    [
        (b"\xff", UnicodeDecodeError, "valid UTF-8 text"),
        (b"invalid JSON", json.JSONDecodeError, "valid JSON data"),
        (b"[]", ValidationError, "expected alias configuration format"),
        (b"{}", ValidationError, "local_aliases"),
    ],
)
def test_load_json_model_wraps_content_errors(
    tmp_path, contents, cause_type, message, capsys
):
    path = tmp_path / "aliases.json"
    path.write_bytes(contents)

    with pytest.raises(ConfigLoadError) as caught:
        load_config_model_from_json_file(
            path=path,
            model=AliasesConfig,
            description="alias configuration",
        )

    assert message in str(caught.value)
    assert str(path) in str(caught.value)
    assert isinstance(caught.value.__cause__, cause_type)
    assert capsys.readouterr().out == ""
