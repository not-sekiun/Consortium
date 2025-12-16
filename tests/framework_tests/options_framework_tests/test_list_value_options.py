import pytest

from consortium.framework.options import ListValueOption
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionConfigurationError,
)


def test_init_with_empty_name():
    with pytest.raises(OptionConfigurationError):
        ListValueOption(
            name="",
            description="This is a test option",
            value_type=int,
            validating_regex=r"^\d+$",
        )


def test_init_with_invalid_type():
    with pytest.raises(OptionConfigurationError):
        ListValueOption(
            name="test_option",
            description="This is a test option",
            value_type=list,
            validating_regex=r"^\d+$",
        )


def test_init_with_valid_params():
    option = ListValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        validating_regex=r"^\d+$",
    )
    assert option.name == "test_option"
    assert option.description == "This is a test option"
    assert option.value_type is int
    assert option.validating_regex == r"^\d+$"
    assert option.allow_duplicates is True


def test_init_with_invalid_default_value():
    with pytest.raises(OptionConfigurationError):
        ListValueOption(
            name="test_option",
            value_type=int,
            default_value=["invalid"],
        )


#
# def test_get_option_value_with_set_value():
#     option = ListValueOption(name="test_option", value_type=int)
#     option.set_option_value([1, 2, 3])
#     assert option.get_option_value() == [1, 2, 3]
#
#
# def test_get_option_value_with_default_value():
#     option = ListValueOption(
#         name="test_option",
#         value_type=int,
#         default_value=[1, 2, 3],
#     )
#     assert option.get_option_value() == [1, 2, 3]
#
#
# def test_required_get_option_value_not_set():
#     option = ListValueOption(name="test_option", value_type=int, required=True)
#     with pytest.raises(RequiredOptionValueNotSetError):
#         option.get_option_value()
#
#
# def test_get_not_required_option_value_not_set():
#     option = ListValueOption(name="test_option", value_type=int, required=False)
#     assert option.get_option_value() is None
#
#
# def test_set_option_value_valid():
#     option = ListValueOption(name="test_option", value_type=int)
#     option.set_option_value([1, 2, 3])
#     assert option.get_option_value() == [1, 2, 3]
#
#
# def test_set_option_value_invalid_type():
#     option = ListValueOption(name="test_option", value_type=int)
#     with pytest.raises(OptionValueValidationError):
#         option.set_option_value(["invalid"])
#
#
# def test_set_option_value_invalid_regex():
#     option = ListValueOption(
#         name="test_option",
#         value_type=str,
#         validating_regex=r"^[a-z]+$",
#     )
#     with pytest.raises(OptionValueValidationError):
#         option.set_option_value(["123", "abc"])
#
#
# def test_set_option_value_invalid_function():
#     def test_function(value):
#         if value > 10:
#             raise OptionValueValidationError("Value is too large")
#
#     option = ListValueOption(
#         name="test_option",
#         value_type=int,
#         validating_function=test_function,
#     )
#     with pytest.raises(OptionValueValidationError):
#         option.set_option_value([5, 20])
#
#
# def test_set_option_value_disallow_duplicates():
#     option = ListValueOption(name="test_option", value_type=int, allow_duplicates=False)
#     with pytest.raises(OptionValueValidationError):
#         option.set_option_value([1, 2, 2])
#
#
# def test_clear_not_required_option_value():
#     option = ListValueOption(name="test_option", value_type=int, required=False)
#     option.set_option_value([1, 2, 3])
#     option.clear_option_value()
#     assert option.get_option_value() is None
#
#
# def test_clear_required_option_value():
#     option = ListValueOption(name="test_option", value_type=int, required=True)
#     option.set_option_value([1, 2, 3])
#     option.clear_option_value()
#     with pytest.raises(RequiredOptionValueNotSetError):
#         option.get_option_value()


def test_to_json():
    def test_function(_value):
        """
        This is a multiline
        test docstring that
        should be formatted
        into a single line.
        """

    option = ListValueOption(
        name="test_option",
        description="This is a test option",
        value_type=int,
        validating_regex=r"^\d+$",
        validating_function=test_function,
        allow_duplicates=False,
    )
    expected_json = {
        "name": "test_option",
        "description": "This is a test option",
        "required": True,
        "default_value": None,
        "allow_duplicates": False,
        "value_type": "int",
        "minimum_length": None,
        "maximum_length": None,
        "less_than": None,
        "greater_than": None,
        "less_than_or_equal_to": None,
        "greater_than_or_equal_to": None,
        "minimum_elements": None,
        "maximum_elements": None,
        "validating_regex": r"^\d+$",
        "validating_function": (
            "This is a multiline test docstring that should be formatted into a single "
            "line."
        ),
        "option_type": "LIST_VALUE_OPTION",
    }
    assert option.to_json() == expected_json
