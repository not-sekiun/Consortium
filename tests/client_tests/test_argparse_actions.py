from argparse import ArgumentParser
from unittest.mock import Mock

import pytest

from consortium.client.repl_interface.argparse_actions import ExtendedHelpAction


@pytest.fixture
def parser():
    parser = ArgumentParser(epilog="Brief help")
    parser.add_argument("value")
    parser.add_argument("--count", type=int)
    parser.add_argument(
        "--help-full",
        action=ExtendedHelpAction,
        epilog="Extended examples",
    )
    return parser


def test_extended_help_works_without_required_arguments_and_preserves_normal_help(
    parser, capsys
):
    with pytest.raises(SystemExit) as raised:
        parser.parse_args(["--help-full"])

    assert raised.value.code == 0
    assert "Extended examples" in capsys.readouterr().out

    with pytest.raises(SystemExit) as raised:
        parser.parse_args(["--help"])

    assert raised.value.code == 0
    output = capsys.readouterr().out
    assert "Brief help" in output
    assert "Extended examples" not in output


@pytest.mark.parametrize(
    ("arguments", "exit_code"),
    [
        (["--count", "invalid", "--help-full"], 2),
        (["--help-full", "--count", "invalid"], 0),
    ],
)
def test_extended_help_follows_argument_processing_order(
    parser, arguments, exit_code, capsys
):
    with pytest.raises(SystemExit) as raised:
        parser.parse_args(arguments)

    assert raised.value.code == exit_code
    output = capsys.readouterr()
    if exit_code:
        assert "invalid int value" in output.err
        assert "Extended examples" not in output.out
    else:
        assert "Extended examples" in output.out
        assert not output.err


def test_extended_help_after_double_dash_is_a_positional_value(parser, capsys):
    parsed_args = parser.parse_args(["--", "--help-full"])

    assert parsed_args.value == "--help-full"
    assert not hasattr(parsed_args, "help_full")
    assert not capsys.readouterr().out


def test_extended_help_restores_epilog_when_rendering_fails(parser, monkeypatch):
    monkeypatch.setattr(parser, "print_help", Mock(side_effect=RuntimeError("rendering")))

    with pytest.raises(RuntimeError, match="rendering"):
        parser.parse_args(["--help-full"])

    assert parser.epilog == "Brief help"
