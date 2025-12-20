import pytest

from consortium.framework.options import ChoiceValueOption
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionConfigurationError,
)


def test_init_with_empty_name():
    with pytest.raises(OptionConfigurationError):
        ChoiceValueOption(
            name="",
            description="This is a test option",
            available_values={"red", "green", "blue"},
        )


def test_init_with_empty_choices():
    with pytest.raises(OptionConfigurationError):
        ChoiceValueOption(
            name="",
            description="This is a test option",
            available_values=set(),
        )


def test_init_with_valid_params():
    option = ChoiceValueOption(
        name="test_option",
        description="This is a test option",
        available_values={"red", "green", "blue"},
    )
    assert option.name == "test_option"
    assert option.description == "This is a test option"
    assert option.available_values == {"red", "green", "blue"}


def test_init_with_invalid_default_value():
    with pytest.raises(OptionConfigurationError):
        ChoiceValueOption(
            name="test_option",
            available_values={"red", "green", "blue"},
            default_value="invalid",
        )


#
# def test_get_option_value_with_set_value():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#     )
#     option.set_option_value("green")
#     assert option.get_option_value() == "green"
#
#
# def test_get_option_value_with_default_value():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#         default_value="red",
#     )
#     assert option.get_option_value() == "red"
#
#
# def test_get_option_value_required_not_set():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#         required=True,
#     )
#     with pytest.raises(RequiredOptionValueNotSetError):
#         option.get_option_value()
#
#
# def test_get_option_value_not_required_not_set():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#         required=False,
#     )
#     assert option.get_option_value() is None
#
#
# def test_set_option_value_valid():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#     )
#     option.set_option_value("green")
#     assert option.get_option_value() == "green"
#
#
# def test_set_option_value_invalid():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#     )
#     with pytest.raises(OptionValueValidationError):
#         option.set_option_value("invalid")
#
#
# def test_clear_not_required_option_value():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#         required=False,
#     )
#     option.set_option_value("green")
#     option.clear_option_value()
#     assert option.get_option_value() is None
#
#
# def test_clear_required_option_value():
#     option = ChoiceValueOption(
#         name="test_option",
#         available_values={"red", "green", "blue"},
#         required=True,
#     )
#     option.set_option_value("green")
#     option.clear_option_value()
#     with pytest.raises(RequiredOptionValueNotSetError):
#         option.get_option_value()


def test_to_json():
    option = ChoiceValueOption(
        name="test_option",
        description="This is a test option",
        available_values={"red", "green", "blue"},
        default_value="red",
    )
    expected_json = {
        "name": "test_option",
        "description": "This is a test option",
        "required": True,
        "default_value": "red",
        "available_values": ["red", "green", "blue"],
        "option_type": "CHOICE_VALUE_OPTION",
    }
    option_json = option.to_json()

    # Sets don't preserve order when converted to lists, so we need to sort the
    # `available_value` array for both the expected and actual json.
    expected_json["available_values"].sort()
    option_json["available_values"].sort()

    assert expected_json == option_json
