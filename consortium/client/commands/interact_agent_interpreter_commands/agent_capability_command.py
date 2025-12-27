from argparse import ArgumentParser
from enum import StrEnum
from typing import Any

from consortium.client.client_rest_api import RestApi
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import (
    print_error,
    print_info,
    print_success,
    print_warning,
)


class _OptionType(StrEnum):
    SINGLE_VALUE_OPTION = "SINGLE_VALUE_OPTION"
    LIST_VALUE_OPTION = "LIST_VALUE_OPTION"
    CHOICE_VALUE_OPTION = "CHOICE_VALUE_OPTION"
    TOGGLEABLE_CHOICES_VALUE_OPTION = "TOGGLEABLE_CHOICES_VALUE_OPTION"
    DICTIONARY_VALUE_OPTION = "DICTIONARY_VALUE_OPTION"


class _OptionValueType(StrEnum):
    STRING = "str"
    INTEGER = "int"
    FLOATING_POINT = "float"
    BOOLEAN = "bool"


def _generate_abbreviated_flags_from_option_name_list(
    option_name_list: list[str],
) -> dict[str, str]:
    flags = {}
    conflicts = []

    # Assign single-letter flags where possible on the first pass.
    for name in option_name_list:
        if "-" + name[0].lower() not in flags.values():
            flags[name] = f"-{name[0].lower()}"
        else:
            conflicts.append(name)

    # Resolve conflicts on the second pass by finding the next available flag.
    for name in conflicts:
        for index in range(1, len(name)):
            if name[: index + 1].lower() not in [v[1:] for v in flags.values()]:
                flags[name] = f"-{name[: index + 1].lower()}"
                break
        else:
            flags[name] = f"-{name.lower()}"

    return flags


# Command objects need to be constructed dynamically based on the agent capabilities
# that are present.
def construct_agent_capability_command(
    agent_capability: dict[str, Any],
) -> BaseCommand:
    class AgentCapabilityCommand(BaseCommand):
        name = agent_capability["name"]
        description = agent_capability["description"]
        epilog = format_argparse_epilog(
            f"""
            Value Type Specification:
              Option values are strings by default. Specify types using:
                1. Inline annotation: value:type (e.g., "3:int")
                2. --value-type flag: applies to all values unless overridden
                3. Option default: used if no type specified

              The --value-type flag applies to all elements in lists/dictionaries.

            Examples:
              # Single values
              {agent_capability["name"]} --<param> 1                    # String "1" (or option's default type)
              {agent_capability["name"]} --<param> 1:int                # Integer 1
              {agent_capability["name"]} --<param> 1 -t int             # Integer 1 (equivalent)
              {agent_capability["name"]} --<param> text:str:str         # String "text:str" (escape colons)

              # Choice values
              {agent_capability["name"]} --<param> choice1              # Implicit type conversion
              {agent_capability["name"]} --<param> 1 -t int             # Exact match required (no conversion)

              # Lists
              {agent_capability["name"]} --<param> 1 2 3:int            # ["1", "2", 3]
              {agent_capability["name"]} --<param> 1 2 3 -t int         # [1, 2, 3]
              {agent_capability["name"]} --<param> 1 2 3:str -t int     # [1, 2, "3"]

              # Dictionaries
              {agent_capability["name"]} --<param> k1 1 k2 2:str -t int # {{k1: 1, k2: "2"}}

              # Toggleable choices (default: toggle specified to True, rest to False)
              {agent_capability["name"]} --<param> c1 c2                # c1=True, c2=True, others=False
              {agent_capability["name"]} --<param> false:bool c1        # c1=False, others=True
              {agent_capability["name"]} --<param> true:bool            # All choices=True
              {agent_capability["name"]} --<param> t:bool               # All choices=True (t/f/1/0 accepted)
              {agent_capability["name"]} --<param> 0 -t bool            # All choices=False
            """,
        )
        group = "Agent Capability Commands"

        def configure_parser(self, parser: ArgumentParser) -> None:
            options = agent_capability["options"]

            # The parser checks to see if there is only one required option for an
            # agent capability. If there is, that one required option is registered to
            # the parser as a positional argument for convenience.
            number_of_required_options = 0
            for _, option in options.items():
                if option["required"]:
                    number_of_required_options += 1

            # If there is one required option we only configure remaining non
            # required options as optional options.
            if number_of_required_options == 1:
                abbreviated_flags = _generate_abbreviated_flags_from_option_name_list(
                    [name for name in options.keys() if not options[name]["required"]],
                )
            else:
                abbreviated_flags = _generate_abbreviated_flags_from_option_name_list(
                    list(options),
                )

            for name, option in options.items():
                # Configure the number of arguments that the parser expects for a
                # particular agent capability based on the option type in the
                # options json data.
                if option["option_type"] in (
                    _OptionType.SINGLE_VALUE_OPTION,
                    _OptionType.CHOICE_VALUE_OPTION,
                ):
                    nargs = "?"
                elif option["option_type"] in (
                    _OptionType.LIST_VALUE_OPTION,
                    _OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION,
                    _OptionType.DICTIONARY_VALUE_OPTION,
                ):
                    nargs = "*"
                else:
                    raise AssertionError(
                        f"Unknown option type {option['option_type']} was present "
                        f"for the option '{option['name']}' in the list of options "
                        f"for the agent capability '{agent_capability['name']}'."
                    )

                # Determine the type of the argument based on the value type in the
                # options json data.
                string_to_type_map = {
                    _OptionValueType.STRING: str,
                    _OptionValueType.INTEGER: int,
                    _OptionValueType.FLOATING_POINT: float,
                    _OptionValueType.BOOLEAN: bool,
                }
                if option["option_type"] in (
                    _OptionType.SINGLE_VALUE_OPTION,
                    _OptionType.CHOICE_VALUE_OPTION,
                ):
                    value_type = string_to_type_map[option["value_type"]]
                elif option["option_type"] in (
                    _OptionType.LIST_VALUE_OPTION,
                    _OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION,
                    _OptionType.DICTIONARY_VALUE_OPTION,
                ):
                    value_type = None
                else:
                    raise AssertionError(
                        f"Unknown value type {option['value_type']} was present "
                        f"for the option '{option['name']}' in the list of options "
                        f"for the agent capability '{agent_capability['name']}'."
                    )

                # For the special case of a single value option with a boolean value
                # type we allow the passing of the flag itself to automatically set the
                # value to `True`.
                if (
                    option["option_type"] == _OptionType.SINGLE_VALUE_OPTION
                    and option["value_type"] == _OptionValueType.BOOLEAN
                ):
                    if number_of_required_options == 1 and option["required"]:
                        parser.add_argument(
                            name,
                            help=option["description"],
                            action="store_true"
                            if option["default_value"]
                            else "store_false",
                            default=option["default_value"],
                        )
                    else:
                        parser.add_argument(
                            abbreviated_flags[name],
                            f"--{name}",
                            help=option["description"],
                            action="store_true"
                            if option["default_value"]
                            else "store_false",
                            required=option["required"],
                            default=option["default_value"],
                        )
                    continue

                # Add the arguments to the parser for every other kind of option
                # specified in the agent capability json data.
                if number_of_required_options == 1 and option["required"]:
                    parser.add_argument(
                        name,
                        help=option["description"],
                        nargs=nargs,
                        type=value_type,
                        # For `nargs` being set to `"?"` there are two possibilities
                        # when it comes to assigning default values. When the flag is
                        # passed but no argument is passed the value from `default` is
                        # used, when the flag is not passed at all, the value from
                        # `const` is used. We make no distinction here so we use the
                        # exact same value.
                        default=option["default_value"],
                        const=option["default_value"] if nargs == "?" else None,
                    )
                else:
                    parser.add_argument(
                        abbreviated_flags[name],
                        f"--{name}",
                        help=option["description"],
                        nargs=nargs,
                        type=value_type,
                        required=option["required"],
                        # For `nargs` being set to `"?"` there are two possibilities
                        # when it comes to assigning default values. When the flag is
                        # passed but no argument is passed the value from `default` is
                        # used, when the flag is not passed at all, the value from
                        # `const` is used. We make no distinction here so we use the
                        # exact same value.
                        default=option["default_value"],
                        const=option["default_value"] if nargs == "?" else None,
                    )

        @staticmethod
        def _check_value_for_value_type_annotation(
            value: str,
        ) -> tuple[str, str | None]:
            # No type annotation is present in the value.
            if ":" not in value:
                return value, None

            value_type = value.split(":")[-1]
            # If the value type is not one of the valid value types, we return the
            # value as is and set the value type to None.
            if value_type == "str":
                return ":".join(value.split(":")[:-1]), "str"
            elif value_type == "int":
                return ":".join(value.split(":")[:-1]), "int"
            elif value_type == "float":
                return ":".join(value.split(":")[:-1]), "float"
            elif value_type == "bool":
                return ":".join(value.split(":")[:-1]), "bool"
            else:
                return value, None

        @staticmethod
        def _convert_value_type(
            value: str,
            value_type: str,
        ) -> str | int | float | bool | list:
            try:
                if value_type == "str":
                    return value
                elif value_type == "int":
                    return int(value)
                elif value_type == "float":
                    return float(value)
                elif value_type == "bool":
                    # bool() of any string is True.
                    if value in {"true", "True", "t", "T", "1"}:
                        return True
                    elif value in {"false", "False", "f", "F", "0"}:
                        return False
                    else:
                        raise ValueError
            except ValueError:
                raise ValueError(
                    f"Failed to convert value '{value}' to type '{value_type}'",
                ) from None

        @staticmethod
        def _resolve_value_type_from_overriding_factors(
            value_type_flag: str | None,
            value_type_annotation: str | None,
            agent_template_option: dict,
        ) -> str:
            # By default, if no overriding factors such as the options supplied value type,
            # the value type flag, or the value type annotation are present, we default to
            # string.
            value_type = "str"
            # Check if an option already specified its type.
            if agent_template_option["value_type"] is not None:
                value_type = agent_template_option["value_type"]
            # Check if the user supplied a value type flag to override the option supplied
            # value type or to explicitly set the value type.
            if value_type_flag is not None:
                value_type = value_type_flag
            # Check if the user supplied a value type annotation to override the value type
            # flag or to explicitly set the value type.
            if value_type_annotation is not None:
                value_type = value_type_annotation

            return value_type

        async def _handle_single_value_parameter(
            self,
            parameter_name: str,
            parameter_value: str | int | float | bool,
            value_type_flag: str | None,
            agent_generator_id: str,
            agent_template_option: dict,
            client_rest_api_connection: RestApi,
        ) -> None:
            parameter_value, value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=parameter_value,
                )
            )
            value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_type_annotation,
                agent_template_option=agent_template_option,
            )
            parameter_value = self._convert_value_type(
                value=parameter_value,
                value_type=value_type,
            )

            if (
                agent_template_option["value_type"] is not None
                and value_type != agent_template_option["value_type"]
            ):
                print_warning(
                    f"Value '{parameter_value}' of type '{value_type}' is not of the "
                    f"expected type '{agent_template_option['value_type']}' for option "
                    f"'{parameter_name}'. However, the value was still set as the user "
                    f"supplied type '{value_type}'.",
                )
            await (
                client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: parameter_value},
                    },
                )
            )
            print_success(
                f"Set agent generator parameter '{parameter_name}' to '{parameter_value}' "
                f"with type '{value_type}'.",
            )

        async def _handle_choice_value_parameter(
            self,
            parameter_name: str,
            parameter_value: str | int | float | bool,
            value_type_flag: str,
            agent_generator_id: str,
            agent_template_option: dict,
            client_rest_api_connection: RestApi,
        ) -> None:
            parameter_value, value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=parameter_value,
                )
            )
            value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_type_annotation,
                agent_template_option=agent_template_option,
            )
            parameter_value = self._convert_value_type(
                value=parameter_value,
                value_type=value_type,
            )

            # If no type was explicitly specified we perform implicit type conversions to
            # check against the string value of each choice.
            if (
                value_type == "str"
                and value_type_flag is None
                and value_type_annotation is None
            ):
                for choice in agent_template_option["available_values"]:
                    if parameter_value == str(choice):
                        await client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                            agent_generator_id=agent_generator_id,
                            new_agent_generator_attributes={
                                "parameters": {parameter_name: parameter_value},
                            },
                        )
                        print_success(
                            f"Set agent generator parameter '{parameter_name}' to "
                            f"'{parameter_value}'",
                        )
                        return
                print_error(
                    f"Value '{parameter_value}' is not a valid choice for parameter "
                    f"'{parameter_name}'. Valid choices are: "
                    f"{', '.join(agent_template_option['available_values'])}",
                )
                return

            # In every other case when a value type is explicitly specified (even if that
            # value type is a string) we do the comparison without any implicit type
            # conversions.
            if parameter_value not in agent_template_option["available_values"]:
                print_error(
                    f"Value '{parameter_value}' is not a valid choice for parameter "
                    f"'{parameter_name}'. Valid choices are: "
                    f"{', '.join(agent_template_option['available_values'])}",
                )
                return
            await (
                client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: parameter_value},
                    },
                )
            )
            print_success(
                f"Set agent generator parameter '{parameter_name}' to "
                f"'{parameter_value}'",
            )

        async def _handle_list_value_parameter(
            self,
            parameter_name: str,
            parameter_values: list[str | int | float | bool],
            value_type_flag: str,
            agent_generator_id: str,
            agent_template_option: dict,
            client_rest_api_connection: RestApi,
        ) -> None:
            new_parameter_values = []
            for parameter_value in parameter_values:
                parameter_value, value_type_annotation = (
                    self._check_value_for_value_type_annotation(
                        value=parameter_value,
                    )
                )
                value_type = self._resolve_value_type_from_overriding_factors(
                    value_type_flag=value_type_flag,
                    value_type_annotation=value_type_annotation,
                    agent_template_option=agent_template_option,
                )
                parameter_value = self._convert_value_type(
                    value=parameter_value,
                    value_type=value_type,
                )

                if (
                    agent_template_option["value_type"] is not None
                    and value_type != agent_template_option["value_type"]
                ):
                    print_warning(
                        f"Value '{parameter_value}' of type '{value_type}' is not of the "
                        f"expected type '{agent_template_option['value_type']}' for "
                        f"option '{parameter_name}'. However, the value was still set as "
                        f"the user supplied type '{value_type}'",
                    )

                new_parameter_values.append(parameter_value)

            await (
                client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: new_parameter_values},
                    },
                )
            )
            print_success(
                f"Set agent generator parameter '{parameter_name}' to "
                f"{agent_template_option['value']!r}",
            )

        async def _handle_dictionary_value_parameter(
            self,
            parameter_name: str,
            parameter_values: list[str | int | float | bool],
            value_type_flag: str,
            agent_generator_id: str,
            agent_template_option: dict,
            client_rest_api_connection: RestApi,
        ) -> None:
            new_agent_generator_parameter = {}
            for index in range(0, len(parameter_values), 2):
                key = parameter_values[index]
                value = parameter_values[index + 1]

                key, key_value_type_annotation = (
                    self._check_value_for_value_type_annotation(
                        value=key,
                    )
                )
                key_value_type = self._resolve_value_type_from_overriding_factors(
                    value_type_flag=value_type_flag,
                    value_type_annotation=key_value_type_annotation,
                    agent_template_option=agent_template_option,
                )
                key = self._convert_value_type(
                    value=key,
                    value_type=key_value_type,
                )
                if key_value_type != "str":
                    print_error(
                        f"Key '{key}' of type '{key_value_type}' is not of the expected "
                        f"type 'str' for parameter '{parameter_name}'.",
                    )
                    return

                value, value_value_type_annotation = (
                    self._check_value_for_value_type_annotation(
                        value=value,
                    )
                )
                value_value_type = self._resolve_value_type_from_overriding_factors(
                    value_type_flag=value_type_flag,
                    value_type_annotation=value_value_type_annotation,
                    agent_template_option=agent_template_option,
                )
                value = self._convert_value_type(
                    value=value,
                    value_type=value_value_type,
                )

                if (
                    agent_template_option["value_type"] is not None
                    and value_value_type != agent_template_option["value_type"]
                ):
                    print_warning(
                        f"Value '{value}' of type '{value_value_type}' for key '{key}' "
                        f"is not of the expected type "
                        f"'{agent_template_option['value_type']}' for option "
                        f"'{parameter_name}'. However, the value was still set as the user "
                        f"supplied type '{value_value_type}'",
                    )

                new_agent_generator_parameter[key] = value

            await (
                client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: new_agent_generator_parameter},
                    },
                )
            )

        async def _handle_toggleable_choice_value_option(
            self,
            parameter_name: str,
            parameter_values: list[str | int | float | bool],
            value_type_flag: str,
            agent_generator_id: str,
            agent_template_option: dict,
            client_rest_api_connection: RestApi,
        ) -> None:
            new_agent_generator_parameter = {}
            toggled_on_values = []
            toggle_value = True

            # Check for the type of toggling that should occur. Whether we should toggle
            # all to True (only True was provided), toggle all to False (only False was
            # provided), or toggle the provided choices to True or the provided choices to
            # False.
            first_option_value, value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=parameter_values[0],
                )
            )
            value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_type_annotation,
                agent_template_option=agent_template_option,
            )
            first_option_value = self._convert_value_type(
                value=first_option_value,
                value_type=value_type,
            )
            if value_type == "bool" and len(parameter_values) == 1:
                toggle_value = first_option_value
                parameter_values = agent_template_option["available_values"]
            elif value_type == "bool" and len(parameter_values) > 1:
                toggle_value = first_option_value

            for parameter_value in parameter_values:
                parameter_value, value_type_annotation = (
                    self._check_value_for_value_type_annotation(
                        value=parameter_value,
                    )
                )
                value_type = self._resolve_value_type_from_overriding_factors(
                    value_type_flag=value_type_flag,
                    value_type_annotation=value_type_annotation,
                    agent_template_option=agent_template_option,
                )
                if value_type != "str":
                    print_error(
                        f"Value '{parameter_value}' of type '{value_type}' is not of the "
                        f"expected type 'str' for option '{parameter_name}'.",
                    )
                    return
                parameter_value = self._convert_value_type(
                    value=parameter_value,
                    value_type=value_type,
                )
                if parameter_value not in agent_template_option["available_values"]:
                    print_error(
                        f"Value '{parameter_value}' is not a valid choice for option "
                        f"'{parameter_name}'. Valid choices are: "
                        f"{', '.join(agent_template_option['available_values'])}",
                    )
                    return

                toggled_on_values.append(parameter_value)
                new_agent_generator_parameter[parameter_value] = toggle_value

            for choice in agent_template_option["available_values"]:
                if choice not in toggled_on_values:
                    new_agent_generator_parameter[choice] = not toggle_value

            await (
                client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator_id,
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: new_agent_generator_parameter},
                    },
                )
            )

            print_success(
                f"Set agent generator parameter '{parameter_name}' to "
                f"{new_agent_generator_parameter!r}",
            )

        async def run(
            self,
            context: Context,
        ) -> ReturnStatus:
            try:
                parsed_args = self.parser.parse_args(context.arguments)
                client_rest_api_connection = context.environment["rest_api"]
                arguments = vars(parsed_args)
                if arguments is None:
                    arguments = {}
                _success_response = (
                    await client_rest_api_connection.task_agent_by_agent_id(
                        agent_id=context.environment["agent"]["agent_id"],
                        command=self.name,
                        arguments=arguments,
                    )
                )
                print_info(
                    f"Tasked agent '{context.environment['agent']['name']}' "
                    f"({context.environment['agent']['agent_id']})",
                )
            except SystemExit:
                pass

            return ReturnStatus(
                type=ReturnStatusType.CONTINUE,
            )

    return AgentCapabilityCommand()
