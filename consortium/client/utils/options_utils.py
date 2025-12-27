from enum import StrEnum
from typing import Any

from consortium.client.utils.printer_utils import print_warning


class OptionType(StrEnum):
    SINGLE_VALUE_OPTION = "SINGLE_VALUE_OPTION"
    LIST_VALUE_OPTION = "LIST_VALUE_OPTION"
    CHOICE_VALUE_OPTION = "CHOICE_VALUE_OPTION"
    TOGGLEABLE_CHOICES_VALUE_OPTION = "TOGGLEABLE_CHOICES_VALUE_OPTION"
    DICTIONARY_VALUE_OPTION = "DICTIONARY_VALUE_OPTION"


def _parse_value_string_for_value_type_annotation(
    value_string: str,
) -> tuple[str, str | None]:
    # No value type annotation is present in the value string.
    if ":" not in value_string:
        return value_string, None

    value_type = value_string.split(":")[-1]
    # If the value type is not one of the valid value types, we return the value as
    # is and set the value type to None.
    if value_type == "str":
        return ":".join(value_string.split(":")[:-1]), "str"
    elif value_type == "int":
        return ":".join(value_string.split(":")[:-1]), "int"
    elif value_type == "float":
        return ":".join(value_string.split(":")[:-1]), "float"
    elif value_type == "bool":
        return ":".join(value_string.split(":")[:-1]), "bool"
    else:
        return value_string, None


def _convert_value_string_from_string_representation_based_on_value_type(
    value_string: str,
    value_type: str,
) -> str | int | float | bool | list:
    try:
        if value_type == "str":
            return value_string
        elif value_type == "int":
            return int(value_string)
        elif value_type == "float":
            return float(value_string)
        elif value_type == "bool":
            # bool() of any string is True.
            if value_string in {"true", "True", "t", "T", "1"}:
                return True
            elif value_string in {"false", "False", "f", "F", "0"}:
                return False
            else:
                raise ValueError(
                    f"Invalid value '{value_string}' provided for a value type of bool",
                ) from None
    except ValueError:
        raise ValueError(
            f"Failed to convert value '{value_string}' to type '{value_type}'",
        ) from None


def _resolve_value_type_from_overriding_factors(
    value_type_flag: str | None,
    value_type_annotation: str | None,
    option_specified_value_type: str | None,
) -> str:
    # By default, if no overriding factors such as the options supplied value type,
    # the value type flag, or the value type annotation are present, we default to
    # string.
    value_type = "str"
    # Check if an option already specified its type.
    if option_specified_value_type is not None:
        value_type = option_specified_value_type
    # Check if the user supplied a value type flag to override the option supplied
    # value type or to explicitly set the value type.
    if value_type_flag is not None:
        value_type = value_type_flag
    # Check if the user supplied a value type annotation to override the value type
    # flag or to explicitly set the value type.
    if value_type_annotation is not None:
        value_type = value_type_annotation

    return value_type


def _handle_single_value_option_parameter(
    value_string: str,
    value_type_flag: str | None,
    option_json_data: dict[str, Any],
) -> tuple[str, str | int | float | bool]:
    value_string, value_type_annotation = _parse_value_string_for_value_type_annotation(
        value_string=value_string,
    )
    value_type = _resolve_value_type_from_overriding_factors(
        value_type_flag=value_type_flag,
        value_type_annotation=value_type_annotation,
        option_specified_value_type=option_json_data["value_type"],
    )
    value_string = _convert_value_string_from_string_representation_based_on_value_type(
        value_string=value_string,
        value_type=value_type,
    )

    if (
        option_json_data["value_type"] is not None
        and value_type != option_json_data["value_type"]
    ):
        print_warning(
            f'Value "{value_string}" of type "{value_type}" is not of the '
            f'expected type "{option_json_data["value_type"]}" for option '
            f'"{option_json_data["name"]}". However, the value was still set as the '
            f'user supplied type "{value_type}".',
        )

    return option_json_data["name"], value_string


def _handle_list_value_option_parameter(
    value_strings: list[str],
    value_type_flag: str,
    option_json_data: dict[str, Any],
) -> tuple[str, list[str | int | float | bool]]:
    new_values = []
    for element in value_strings:
        element, element_type_annotation = (
            _parse_value_string_for_value_type_annotation(
                value_string=element,
            )
        )
        element_type = _resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=element_type_annotation,
            option_specified_value_type=option_json_data["value_type"],
        )
        element = _convert_value_string_from_string_representation_based_on_value_type(
            value_string=element,
            value_type=element_type,
        )

        if (
            option_json_data["value_type"] is not None
            and element_type != option_json_data["value_type"]
        ):
            print_warning(
                f'Value "{element}" of type "{element_type}" is not of the '
                f'expected type "{option_json_data["value_type"]}" for '
                f'option "{option_json_data["name"]}". However, the value was still '
                f'set as the user supplied type "{element_type}"',
            )

        new_values.append(element)

    return option_json_data["name"], new_values


def _handle_choice_value_option_parameter(
    value_string: str,
    value_type_flag: str,
    option_json_data: dict,
) -> tuple[str, str | int | float | bool]:
    value_string, value_type_annotation = _parse_value_string_for_value_type_annotation(
        value_string=value_string,
    )
    value_type = _resolve_value_type_from_overriding_factors(
        value_type_flag=value_type_flag,
        value_type_annotation=value_type_annotation,
        option_specified_value_type=option_json_data["value_type"],
    )
    value = _convert_value_string_from_string_representation_based_on_value_type(
        value_string=value_string,
        value_type=value_type,
    )

    # If no type was explicitly specified we perform implicit type conversions to
    # check against the string value of each choice.
    if (
        value_type == "str"
        and value_type_flag is None
        and value_type_annotation is None
    ):
        for choice in option_json_data["available_values"]:
            if value == str(choice):
                return option_json_data["name"], choice
        raise ValueError(
            f"Failed to set option '{option_json_data['name']}' to value '{value}'. "
            f"The provided value is not a valid choice. Valid choices are: "
            f"{', '.join(f"'{option_json_data['available_values']}'")}",
        )

    # In every other case when a value type is explicitly specified (even if that
    # value type is a string) we do the comparison without any implicit type
    # conversions.
    if value not in option_json_data["available_values"]:
        raise ValueError(
            f"Failed to set option '{option_json_data['name']}' to value '{value}'. "
            f"The provided value is not a valid choice. Valid choices are: "
            f"{', '.join(f"'{option_json_data['available_values']}'")}",
        )

    return option_json_data["name"], value


def _handle_dictionary_value_option_parameter(
    value_strings: list[str | int | float | bool],
    value_type_flag: str,
    option_json_data: dict,
) -> tuple[str, dict[str, str | int | float | bool]]:
    new_agent_generator_parameter = {}
    for index in range(0, len(value_strings), 2):
        key_string = value_strings[index]
        dict_value_string = value_strings[index + 1]

        # Keys are only ever supposed to be strings so if the user supplied input
        # purposefully attempts to set a key to a type other than a string, we raise
        # an error.
        key_string, key_value_type_annotation = (
            _parse_value_string_for_value_type_annotation(
                value_string=key_string,
            )
        )
        key_value_type = _resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=key_value_type_annotation,
            option_specified_value_type=option_json_data["value_type"],
        )

        if key_value_type != "str":
            raise ValueError(
                f"Failed to set option '{option_json_data['name']}' to value "
                f"'{value_strings}'. Key '{key_string}' of type '{key_value_type}' is "
                f"not of the expected type 'str'. All keys for dictionary options must "
                f"be of type 'str'.",
            )

        dict_value_string, dict_value_type_annotation = (
            _parse_value_string_for_value_type_annotation(
                value_string=dict_value_string,
            )
        )
        dict_value_type = _resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=dict_value_type_annotation,
            option_specified_value_type=option_json_data["value_type"],
        )
        dict_value = (
            _convert_value_string_from_string_representation_based_on_value_type(
                value_string=dict_value_string,
                value_type=dict_value_type,
            )
        )

        if (
            option_json_data["value_type"] is not None
            and dict_value_type != option_json_data["value_type"]
        ):
            print_warning(
                f"Value '{dict_value}' of type '{dict_value_type}' for key "
                f"'{key_string}' is not of the expected type "
                f"'{option_json_data['value_type']}' for option "
                f"'{option_json_data['name']}'. However, the value was still set as "
                f"the user supplied type '{dict_value_string}'.",
            )

        new_agent_generator_parameter[key_string] = dict_value

    return option_json_data["name"], new_agent_generator_parameter


def _handle_toggleable_choice_value_option_parameter(
    value_strings: list[str | int | float | bool],
    value_type_flag: str,
    option_json_data: dict[str, Any],
) -> tuple[str, dict[str, bool]]:
    new_agent_generator_parameter = {}
    toggled_on_values = []
    toggle_value = True

    # Check for the type of toggling that should occur. Whether we should toggle
    # all to True (only True was provided), toggle all to False (only False was
    # provided), or toggle the provided choices to True or the provided choices to
    # False.
    first_option_value_string, value_type_annotation = (
        _parse_value_string_for_value_type_annotation(
            value_string=value_strings[0],
        )
    )
    value_type = _resolve_value_type_from_overriding_factors(
        value_type_flag=value_type_flag,
        value_type_annotation=value_type_annotation,
        option_specified_value_type=option_json_data["value_type"],
    )
    first_option_value = (
        _convert_value_string_from_string_representation_based_on_value_type(
            value_string=first_option_value_string,
            value_type=value_type,
        )
    )
    if value_type == "bool" and len(value_strings) == 1:
        toggle_value = first_option_value
        value_strings = option_json_data["available_values"]
    elif value_type == "bool" and len(value_strings) > 1:
        toggle_value = first_option_value

    for parameter_value_string in value_strings:
        parameter_value_string, value_type_annotation = (
            _parse_value_string_for_value_type_annotation(
                value_string=parameter_value_string,
            )
        )
        value_type = _resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=value_type_annotation,
            option_specified_value_type=option_json_data["value_type"],
        )
        # The value type of all choices should be strings for toggleable choices
        # because those dictate the names of the choices that will be toggled to a
        # specific boolean value.
        if value_type != "str":
            raise ValueError(
                f"Failed to set option '{option_json_data['name']}'. Value "
                f"'{parameter_value_string}' of type '{value_type}' is not of the "
                f"expected type 'str'. All choices for toggleable options must be of "
                f"type 'str'.",
            )
        parameter_value_string = (
            _convert_value_string_from_string_representation_based_on_value_type(
                value_string=parameter_value_string,
                value_type=value_type,
            )
        )
        if parameter_value_string not in option_json_data["available_values"]:
            raise ValueError(
                f"Failed to set option '{option_json_data['name']}' to value "
                f"'{parameter_value_string}'. The provided value is not a valid "
                f"choice. Valid choices are: "
                f"{', '.join(f"'{option_json_data['available_values']}'")}.",
            )

        toggled_on_values.append(parameter_value_string)
        new_agent_generator_parameter[parameter_value_string] = toggle_value

    for choice in option_json_data["available_values"]:
        if choice not in toggled_on_values:
            new_agent_generator_parameter[choice] = not toggle_value

    return option_json_data["name"], new_agent_generator_parameter


def convert_option_value_strings_to_option_value(
    option_json_data: dict[str, Any],
    value_strings: list[str],
    value_type_flag: str,
) -> tuple[str, Any]:
    if option_json_data["option_type"] == OptionType.SINGLE_VALUE_OPTION:
        if len(value_strings) != 1:
            raise ValueError(
                f"Expected 1 value for option '{option_json_data['name']}' of option "
                f"type '{option_json_data['option_type']}' but got "
                f"{len(value_strings)} values instead.",
            )
        return _handle_single_value_option_parameter(
            value_string=value_strings[0],
            value_type_flag=value_type_flag,
            option_json_data=option_json_data,
        )
    elif option_json_data["option_type"] == OptionType.LIST_VALUE_OPTION:
        return _handle_list_value_option_parameter(
            value_strings=value_strings,
            value_type_flag=value_type_flag,
            option_json_data=option_json_data,
        )
    elif option_json_data["option_type"] == OptionType.CHOICE_VALUE_OPTION:
        if len(value_strings) != 1:
            raise ValueError(
                f"Expected 1 value for option '{option_json_data['name']}' of option "
                f"type '{option_json_data['option_type']}' but got "
                f"{len(value_strings)} values instead.",
            )
        return _handle_choice_value_option_parameter(
            value_string=value_strings[0],
            value_type_flag=value_type_flag,
            option_json_data=option_json_data,
        )
    elif option_json_data["option_type"] == OptionType.DICTIONARY_VALUE_OPTION:
        if len(value_strings) % 2 != 0:
            raise ValueError(
                f"Expected an even number of values for "
                f"option '{option_json_data['name']}' of option type "
                f"'{option_json_data['option_type']}' but got "
                f"{len(value_strings)} values instead.",
            )
        return _handle_dictionary_value_option_parameter(
            value_strings=value_strings,
            value_type_flag=value_type_flag,
            option_json_data=option_json_data,
        )
    elif option_json_data["option_type"] == OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION:
        if len(value_strings) < 1:
            raise ValueError(
                f"Expected at least 1 value for option "
                f"'{option_json_data['name']}' of option type "
                f"'{option_json_data['option_type']}' but got {len(value_strings)} "
                f"values instead.",
            )
        return _handle_toggleable_choice_value_option_parameter(
            value_strings=value_strings,
            value_type_flag=value_type_flag,
            option_json_data=option_json_data,
        )
    else:
        raise AssertionError(
            f"Failed to set option '{option_json_data['name']}'. The option type "
            f"'{option_json_data['option_type']}' is not valid."
        )
