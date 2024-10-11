import pytest

from consortium.framework.options import ToggleableChoicesValueOption
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionConfigurationError,
    OptionValueValidationError,
    RequiredOptionValueNotSetError,
)


def test_init_with_empty_name():
    with pytest.raises(OptionConfigurationError):
        ToggleableChoicesValueOption(
            name="",
            description="This is a test option",
            available_values={"red", "green", "blue"},
        )


def test_init_with_empty_choices():
    with pytest.raises(OptionConfigurationError):
        ToggleableChoicesValueOption(
            name="",
            description="This is a test option",
            available_values=set(),
        )


def test_init_with_valid_params():
    option = ToggleableChoicesValueOption(
        name="test_option",
        description="This is a test option",
        available_values={"choice1", "choice2", "choice3"},
    )
    assert option.name == "test_option"
    assert option.description == "This is a test option"
    assert option.available_values == {"choice1", "choice2", "choice3"}


def test_init_with_invalid_available_values():
    with pytest.raises(OptionConfigurationError):
        ToggleableChoicesValueOption(name="test_option", available_values=set())


def test_init_with_invalid_default_value():
    with pytest.raises(OptionConfigurationError):
        ToggleableChoicesValueOption(
            name="test_option",
            available_values={"choice1", "choice2", "choice3"},
            default_value={"choice1": True, "invalid": False},
        )


def test_get_option_value_with_set_value():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
    )
    option.set_option_value({"choice1": True, "choice2": False, "choice3": True})
    assert option.get_option_value() == {
        "choice1": True,
        "choice2": False,
        "choice3": True,
    }


def test_get_option_value_with_default_value():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
        default_value={"choice1": True, "choice2": False, "choice3": True},
    )
    assert option.get_option_value() == {
        "choice1": True,
        "choice2": False,
        "choice3": True,
    }


def test_get_option_value_required_not_set():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
        required=True,
    )
    with pytest.raises(RequiredOptionValueNotSetError):
        option.get_option_value()


def test_get_option_value_not_required_not_set():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
        required=False,
    )
    assert option.get_option_value() is None


def test_set_option_value_valid():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
    )
    option.set_option_value({"choice1": True, "choice2": False, "choice3": True})
    assert option.get_option_value() == {
        "choice1": True,
        "choice2": False,
        "choice3": True,
    }


def test_set_option_value_invalid_type():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value(["choice1", "choice2"])


def test_set_option_value_invalid_key():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"choice1": True, "invalid": False})


def test_set_option_value_invalid_value():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
    )
    with pytest.raises(OptionValueValidationError):
        option.set_option_value({"choice1": True, "choice2": "invalid"})


def test_clear_required_option_value():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
        required=True,
    )
    option.set_option_value({"choice1": True, "choice2": False, "choice3": True})
    option.clear_option_value()
    with pytest.raises(RequiredOptionValueNotSetError):
        option.get_option_value()


def test_clear_not_required_option_value():
    option = ToggleableChoicesValueOption(
        name="test_option",
        available_values={"choice1", "choice2", "choice3"},
        required=False,
    )
    option.set_option_value({"choice1": True, "choice2": False, "choice3": True})
    option.clear_option_value()
    assert option.get_option_value() is None


def test_to_json():
    option = ToggleableChoicesValueOption(
        name="test_option",
        description="This is a test option",
        available_values={"choice1", "choice2", "choice3"},
        default_value={"choice1": True, "choice2": False, "choice3": True},
    )
    expected_json = {
        "name": "test_option",
        "description": "This is a test option",
        "required": True,
        "default_value": {"choice1": True, "choice2": False, "choice3": True},
        "available_values": ["choice1", "choice2", "choice3"],
        "option_type": "TOGGLEABLE_CHOICES_VALUE_OPTION",
    }
    option_json = option.to_json()

    # Sets don't preserve order when converted to lists, so we need to sort the
    # `available_value` array for both the expected and actual json.
    expected_json["available_values"].sort()
    option_json["available_values"].sort()

    assert option_json == expected_json
