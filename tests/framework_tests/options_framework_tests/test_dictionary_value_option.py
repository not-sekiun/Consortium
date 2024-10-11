import pytest

from consortium.framework.options import DictionaryValueOption
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionConfigurationError,
    OptionValueValidationError,
    RequiredOptionValueNotSetError,
)


def test_init_with_empty_name():
    with pytest.raises(OptionConfigurationError):
        DictionaryValueOption(
            name="",
            description="This is a test option",
            value_type=int,
            key_validating_regex=r"^[a-z]+$",
        )


def test_init_with_valid_params():
    option = DictionaryValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        key_validating_regex=r"^[a-z]+$",
    )
    assert option.name == "test_option"
    assert option.description == "This is a test option"
    assert option.value_type == int
    assert option.key_validating_regex == r"^[a-z]+$"


def test_init_with_invalid_value_type():
    with pytest.raises(OptionConfigurationError):
        DictionaryValueOption(name="test_option", value_type=list)


def test_init_with_invalid_default_value():
    with pytest.raises(OptionConfigurationError):
        DictionaryValueOption(
            name="test_option",
            value_type=int,
            default_value={"key": "invalid"},
        )


def test_get_option_value_with_set_value():
    option = DictionaryValueOption(name="test_option", value_type=int)
    option.set_option_value({"key1": 1, "key2": 2})
    assert option.get_option_value() == {"key1": 1, "key2": 2}


def test_get_option_value_with_default_value():
    option = DictionaryValueOption(
        name="test_option",
        value_type=int,
        default_value={"key1": 1, "key2": 2},
    )
    assert option.get_option_value() == {"key1": 1, "key2": 2}


def test_get_option_value_required_not_set():
    option = DictionaryValueOption(name="test_option", value_type=int, required=True)
    with pytest.raises(RequiredOptionValueNotSetError):
        option.get_option_value()


def test_get_option_value_not_required_not_set():
    option = DictionaryValueOption(name="test_option", value_type=int, required=False)
    assert option.get_option_value() is None


def test_set_option_value_valid():
    option = DictionaryValueOption(name="test_option", value_type=int)
    option.set_option_value({"key1": 1, "key2": 2})
    assert option.get_option_value() == {"key1": 1, "key2": 2}


def test_set_option_value_invalid_type():
    option = DictionaryValueOption(name="test_option", value_type=int)
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"key1": 1, "key2": "invalid"})


def test_set_option_value_invalid_key_type():
    option = DictionaryValueOption(name="test_option", value_type=int)
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({1: 1, 2: 2})


def test_set_option_value_invalid_key_regex():
    option = DictionaryValueOption(
        name="test_option",
        value_type=int,
        key_validating_regex=r"^[a-z]+$",
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"KEY1": 1, "key2": 2})


def test_set_option_value_invalid_key_function():
    def test_function(value):
        if value.startswith("invalid"):
            raise OptionValueValidationError("Invalid key prefix")

    option = DictionaryValueOption(
        name="test_option",
        value_type=int,
        key_validating_function=test_function,
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"invalid_key": 1, "key2": 2})


def test_set_option_value_invalid_value_regex():
    option = DictionaryValueOption(
        name="test_option",
        value_type=str,
        value_validating_regex=r"^[a-z]+$",
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"key1": "ABC", "key2": "def"})


def test_set_option_value_invalid_value_function():
    def test_function(value):
        if value > 10:
            raise OptionValueValidationError("Value is too large")

    option = DictionaryValueOption(
        name="test_option",
        value_type=int,
        value_validating_function=test_function,
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"key1": 5, "key2": 20})


def test_set_option_value_invalid_validating_function():
    def test_function(value):
        if len(value) != 2:
            raise OptionValueValidationError("Dictionary must have two keys")

    option = DictionaryValueOption(
        name="test_option",
        value_type=int,
        validating_function=test_function,
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"key1": 1, "key2": 2, "key3": 3})


def test_clear_not_required_option_value():
    option = DictionaryValueOption(name="test_option", value_type=int, required=False)
    option.set_option_value({"key1": 1, "key2": 2})
    option.clear_option_value()
    assert option.get_option_value() is None


def test_clear_required_option_value():
    option = DictionaryValueOption(name="test_option", value_type=int, required=True)
    option.set_option_value({"key1": 1, "key2": 2})
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

    option = DictionaryValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        key_validating_regex=r"^[a-z]+$",
        key_validating_function=test_function,
        value_validating_regex=r"^\d+$",
        value_validating_function=test_function,
        validating_function=test_function,
    )
    expected_json = {
        "name": "test_option",
        "description": "This is a test option",
        "required": True,
        "default_value": None,
        "key_validating_regex": r"^[a-z]+$",
        "key_validating_function": (
            "This is a multiline test docstring that should be formatted into a single "
            "line."
        ),
        "value_type": "int",
        "value_validating_regex": r"^\d+$",
        "value_validating_function": (
            "This is a multiline test docstring that should be formatted into a single "
            "line."
        ),
        "validating_function": (
            "This is a multiline test docstring that should be formatted into a single "
            "line."
        ),
        "option_type": "DICTIONARY_VALUE_OPTION",
    }
    assert option.to_json() == expected_json
