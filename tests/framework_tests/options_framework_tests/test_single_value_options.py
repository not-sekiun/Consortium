import pytest

from consortium.framework.options import SingleValueOption
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionConfigurationError,
    OptionValueValidationError,
    RequiredOptionValueNotSetError,
)


def test_init_with_empty_name():
    with pytest.raises(OptionConfigurationError):
        SingleValueOption(
            name="",
            description="This is a test option",
            value_type=int,
            validating_regex=r"^\d+$",
        )


def test_init_with_invalid_type():
    with pytest.raises(OptionConfigurationError):
        SingleValueOption(
            name="test_option",
            description="This is a test option",
            value_type=list,
            validating_regex=r"^\d+$",
        )


def test_init_with_valid_params():
    option = SingleValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        validating_regex=r"^\d+$",
    )
    assert option.name == "test_option"
    assert option.description == "This is a test option"
    assert option.value_type == int
    assert option.validating_regex == r"^\d+$"


def test_init_with_invalid_default_value():
    with pytest.raises(OptionConfigurationError):
        SingleValueOption(
            name="test_option",
            value_type=int,
            default_value="invalid",
        )


def test_get_option_value_with_set_value():
    option = SingleValueOption(name="test_option", value_type=int)
    option.set_option_value(42)
    assert option.get_option_value() == 42


def test_get_option_value_with_default_value():
    option = SingleValueOption(name="test_option", value_type=int, default_value=10)
    assert option.get_option_value() == 10


def test_get_required_option_value_not_set():
    option = SingleValueOption(name="test_option", value_type=int, required=True)
    with pytest.raises(RequiredOptionValueNotSetError):
        option.get_option_value()


def test_get_required_option_value_not_not_set():
    option = SingleValueOption(name="test_option", value_type=int, required=False)
    assert option.get_option_value() is None


def test_set_option_value_valid():
    option = SingleValueOption(name="test_option", value_type=int)
    option.set_option_value(42)
    assert option.get_option_value() == 42


def test_set_option_value_invalid_type():
    option = SingleValueOption(name="test_option", value_type=int)
    with pytest.raises(OptionValueValidationError):
        option.set_option_value("invalid")


def test_set_option_value_invalid_regex():
    option = SingleValueOption(
        name="test_option",
        value_type=str,
        validating_regex=r"^[a-z]+$",
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value("123")


def test_set_option_value_invalid_function():
    def test_function(value):
        if value > 10:
            raise OptionValueValidationError("Value is too large")

    option = SingleValueOption(
        name="test_option",
        value_type=int,
        validating_function=test_function,
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value(20)


def test_clear_not_required_option_value():
    option = SingleValueOption(name="test_option", value_type=int, required=False)
    option.set_option_value(42)
    option.clear_option_value()
    assert option.get_option_value() is None


def test_clear_required_option_value():
    option = SingleValueOption(name="test_option", value_type=int, required=True)
    option.set_option_value(42)
    option.clear_option_value()
    with pytest.raises(RequiredOptionValueNotSetError):
        option.get_option_value()


def test_to_json():
    def test_function(_value):
        """
        This is a multiline
        test docstring that
        should be formatted
        into a single line.
        """

    option = SingleValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        validating_regex=r"^\d+$",
        validating_function=test_function,
    )
    expected_json = {
        "name": "test_option",
        "description": "This is a test option",
        "required": True,
        "default_value": None,
        "value_type": "int",
        "validating_regex": r"^\d+$",
        "validating_function": (
            "This is a multiline test docstring that should be formatted into a single "
            "line."
        ),
        "option_type": "SINGLE_VALUE_OPTION",
    }
    assert option.to_json() == expected_json
