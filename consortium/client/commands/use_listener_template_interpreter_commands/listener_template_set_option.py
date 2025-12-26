import copy
from argparse import ArgumentParser

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_set_value_command_epilog
from consortium.client.utils.printer_utils import (
    print_error,
    print_success,
    print_warning,
)


class ListenerTemplateSetOptionCommand(BaseCommand):
    name = "set"
    description = "Set the current listener template's option to a specific value"
    epilog = format_set_value_command_epilog(command_name="set")
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_str",
            help="Name of the listener template option to set the value of.",
            nargs=1,
        )
        parser.add_argument(
            "option_values",
            help="Value to set the listener template option to. The number of provided "
            "values must match the expected number of values for the option based "
            "on the option's option type.",
            nargs="+",
        )
        parser.add_argument(
            "--value-type",
            "-t",
            help="Type of the listener template option to set. When set for a list or "
            "dictionary value type option, all the elements of the list or values "
            "of the dictionary will be set to that same type unless explicitly "
            "specified as otherwise by their individual typing.",
            choices={"str", "int", "float", "bool"},
            nargs="?",
            default=None,
            metavar="VALUE_TYPE",
        )

    @staticmethod
    def _check_value_for_value_type_annotation(
        value: str,
    ) -> tuple[str, str | None]:
        # No type annotation is present in the value.
        if ":" not in value:
            return value, None

        value_type = value.split(":")[-1]
        # If the value type is not one of the valid value types, we return the value as
        # is and set the value type to None.
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
        listener_template_option: dict,
    ) -> str:
        # By default, if no overriding factors such as the options supplied value type,
        # the value type flag, or the value type annotation are present, we default to
        # string.
        value_type = "str"
        # Check if an option already specified its type.
        if listener_template_option["value_type"] is not None:
            value_type = listener_template_option["value_type"]
        # Check if the user supplied a value type flag to override the option supplied
        # value type or to explicitly set the value type.
        if value_type_flag is not None:
            value_type = value_type_flag
        # Check if the user supplied a value type annotation to override the value type
        # flag or to explicitly set the value type.
        if value_type_annotation is not None:
            value_type = value_type_annotation

        return value_type

    def _handle_single_value_option(
        self,
        option_name: str,
        option_value: str | int | float | bool,
        value_type_flag: str | None,
        listener_template_option: dict,
    ) -> None:
        option_value, value_type_annotation = (
            self._check_value_for_value_type_annotation(
                value=option_value,
            )
        )
        value_type = self._resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=value_type_annotation,
            listener_template_option=listener_template_option,
        )
        option_value = self._convert_value_type(
            value=option_value,
            value_type=value_type,
        )

        if (
            listener_template_option["value_type"] is not None
            and value_type != listener_template_option["value_type"]
        ):
            print_warning(
                f'Value "{option_value}" of type "{value_type}" is not of the expected '
                f'type "{listener_template_option["value_type"]}" for option '
                f'"{option_name}". However, the value was still set as the user '
                f'supplied type "{value_type}".',
            )
        listener_template_option["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to '
            f'"{listener_template_option["value"]}" with type "{value_type}".',
        )

    def _handle_choice_value_option(
        self,
        option_name: str,
        option_value: str | int | float | bool,
        value_type_flag: str,
        listener_template_option: dict,
    ) -> None:
        option_value, value_type_annotation = (
            self._check_value_for_value_type_annotation(
                value=option_value,
            )
        )
        value_type = self._resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=value_type_annotation,
            listener_template_option=listener_template_option,
        )
        option_value = self._convert_value_type(
            value=option_value,
            value_type=value_type,
        )

        # If no type was explicitly specified we perform implicit type conversions to
        # check against the string value of each choice.
        if (
            value_type == "str"
            and value_type_flag is None
            and value_type_annotation is None
        ):
            for choice in listener_template_option["available_values"]:
                if option_value == str(choice):
                    listener_template_option["value"] = choice
                    print_success(
                        f'Set listener template option "{option_name}" to '
                        f'"{listener_template_option["value"]}"',
                    )
                    return
            print_error(
                f'Value "{option_value}" is not a valid choice for option '
                f'"{option_name}". Valid choices are: '
                f"{', '.join(listener_template_option['available_values'])}",
            )
            return

        # In every other case when a value type is explicitly specified (even if that
        # value type is a string) we do the comparison without any implicit type
        # conversions.
        if option_value not in listener_template_option["available_values"]:
            print_error(
                f'Value "{option_value}" is not a valid choice for option '
                f'"{option_name}". Valid choices are: '
                f"{', '.join(listener_template_option['available_values'])}",
            )
            return
        listener_template_option["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to '
            f'"{listener_template_option["value"]}"',
        )

    def _handle_list_value_option(
        self,
        option_name: str,
        option_values: list[str | int | float | bool],
        value_type_flag: str,
        listener_template_option: dict,
    ) -> None:
        new_option_values = []
        for option_value in option_values:
            option_value, value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=option_value,
                )
            )
            value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_type_annotation,
                listener_template_option=listener_template_option,
            )
            option_value = self._convert_value_type(
                value=option_value,
                value_type=value_type,
            )

            if (
                listener_template_option["value_type"] is not None
                and value_type != listener_template_option["value_type"]
            ):
                print_warning(
                    f'Value "{option_value}" of type "{value_type}" is not of the '
                    f'expected type "{listener_template_option["value_type"]}" for '
                    f'option "{option_name}". However, the value was still set as the '
                    f'user supplied type "{value_type}"',
                )

            new_option_values.append(option_value)

        listener_template_option["value"] = new_option_values
        print_success(
            f'Set listener template option "{option_name}" to '
            f"{listener_template_option['value']!r}",
        )

    def _handle_dictionary_value_option(
        self,
        option_name: str,
        option_values: list[str | int | float | bool],
        value_type_flag: str,
        listener_template_option: dict,
    ) -> None:
        previous_value = copy.deepcopy(listener_template_option["value"])
        for index in range(0, len(option_values), 2):
            key = option_values[index]
            value = option_values[index + 1]

            key, key_value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=key,
                )
            )
            key_value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=key_value_type_annotation,
                listener_template_option=listener_template_option,
            )
            key = self._convert_value_type(
                value=key,
                value_type=key_value_type,
            )
            if key_value_type != "str":
                print_error(
                    f'Key "{key}" of type "{key_value_type}" is not of the expected '
                    f'type "str" for option "{option_name}".',
                )
                # Changes to the listener template options should be atomic.
                listener_template_option["value"] = copy.deepcopy(previous_value)
                return

            value, value_value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=value,
                )
            )
            value_value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_value_type_annotation,
                listener_template_option=listener_template_option,
            )
            value = self._convert_value_type(
                value=value,
                value_type=value_value_type,
            )

            if (
                listener_template_option["value_type"] is not None
                and value_value_type != listener_template_option["value_type"]
            ):
                print_warning(
                    f'Value "{value}" of type "{value_value_type}" for key "{key}" is '
                    f"not of the expected type "
                    f'"{listener_template_option["value_type"]}" for option '
                    f'"{option_name}". However, the value was still set as the user '
                    f'supplied type "{value_value_type}"',
                )

            listener_template_option["value"][key] = value

    def _handle_toggleable_choice_value_option(
        self,
        option_name: str,
        option_values: list[str | int | float | bool],
        value_type_flag: str,
        listener_template_option: dict,
    ) -> None:
        previous_value = copy.deepcopy(listener_template_option["value"])
        toggled_on_values = []
        toggle_value = True

        # Check for the type of toggling that should occur. Whether we should toggle
        # all to True (only True was provided), toggle all to False (only False was
        # provided), or toggle the provided choices to True or the provided choices to
        # False.
        first_option_value, value_type_annotation = (
            self._check_value_for_value_type_annotation(
                value=option_values[0],
            )
        )
        value_type = self._resolve_value_type_from_overriding_factors(
            value_type_flag=value_type_flag,
            value_type_annotation=value_type_annotation,
            listener_template_option=listener_template_option,
        )
        first_option_value = self._convert_value_type(
            value=first_option_value,
            value_type=value_type,
        )
        if value_type == "bool" and len(option_values) == 1:
            toggle_value = first_option_value
            option_values = listener_template_option["available_values"]
        elif value_type == "bool" and len(option_values) > 1:
            toggle_value = first_option_value

        for option_value in option_values:
            option_value, value_type_annotation = (
                self._check_value_for_value_type_annotation(
                    value=option_value,
                )
            )
            value_type = self._resolve_value_type_from_overriding_factors(
                value_type_flag=value_type_flag,
                value_type_annotation=value_type_annotation,
                listener_template_option=listener_template_option,
            )
            if value_type != "str":
                print_error(
                    f'Value "{option_value}" of type "{value_type}" is not of the '
                    f'expected type "str" for option "{option_name}".',
                )
                # Changes to the listener template options should be atomic.
                listener_template_option["value"] = copy.deepcopy(previous_value)
                return
            option_value = self._convert_value_type(
                value=option_value,
                value_type=value_type,
            )
            if option_value not in listener_template_option["available_values"]:
                print_error(
                    f'Value "{option_value}" is not a valid choice for option '
                    f'"{option_name}". Valid choices are: '
                    f"{', '.join(listener_template_option['available_values'])}",
                )
                # Changes to the listener template options should be atomic.
                listener_template_option["value"] = copy.deepcopy(previous_value)
                return

            toggled_on_values.append(option_value)
            listener_template_option["value"][option_value] = toggle_value

        for choice in listener_template_option["available_values"]:
            if choice not in toggled_on_values:
                listener_template_option["value"][choice] = not toggle_value

        print_success(
            f'Set listener template option "{option_name}" to '
            f"{listener_template_option['value']!r}",
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            listener_template_options = context.environment["listener_template"][
                "options"
            ]

            option_name = parsed_args.option_name[0]
            option_values = parsed_args.option_values
            value_type = parsed_args.value_type
            try:
                option = listener_template_options[option_name]
            except KeyError:
                print_error(
                    f'Listener template option "{option_name}" does not exist.',
                )
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            try:
                if option["option_type"] == "SINGLE_VALUE_OPTION":
                    if len(option_values) != 1:
                        print_error(
                            f"Expected 1 value for listener template option "
                            f'"{option_name}" of option type "{option["option_type"]}" '
                            f"but got {len(option_values)} values instead.",
                        )
                        return ReturnStatus(type=ReturnStatusType.CONTINUE)
                    self._handle_single_value_option(
                        option_name=option_name,
                        option_value=option_values[0],
                        value_type_flag=value_type,
                        listener_template_option=option,
                    )
                elif option["option_type"] == "CHOICE_VALUE_OPTION":
                    if len(option_values) != 1:
                        print_error(
                            f"Expected 1 value for listener template option "
                            f'"{option_name}" of option type "{option["option_type"]}" '
                            f"but got {len(option_values)} values instead.",
                        )
                        return ReturnStatus(type=ReturnStatusType.CONTINUE)
                    self._handle_choice_value_option(
                        option_name=option_name,
                        option_value=option_values[0],
                        value_type_flag=value_type,
                        listener_template_option=option,
                    )
                elif option["option_type"] == "LIST_VALUE_OPTION":
                    self._handle_list_value_option(
                        option_name=option_name,
                        option_values=option_values,
                        value_type_flag=value_type,
                        listener_template_option=option,
                    )
                elif option["option_type"] == "DICTIONARY_VALUE_OPTION":
                    if len(option_values) % 2 != 0:
                        print_error(
                            f"Expected an even number of values for listener template "
                            f'option "{option_name}" of option type '
                            f'"{option["option_type"]}" but got {len(option_values)} '
                            f"values instead.",
                        )
                        return ReturnStatus(type=ReturnStatusType.CONTINUE)
                    self._handle_dictionary_value_option(
                        option_name=option_name,
                        option_values=option_values,
                        value_type_flag=value_type,
                        listener_template_option=option,
                    )
                elif option["option_type"] == "TOGGLEABLE_CHOICES_VALUE_OPTION":
                    if len(option_values) != 1:
                        print_error(
                            f"Expected 1 value for listener template option "
                            f'"{option_name}" of option type "{option["option_type"]}" '
                            f"but got {len(option_values)} values instead.",
                        )
                        return ReturnStatus(type=ReturnStatusType.CONTINUE)
                    self._handle_toggleable_choice_value_option(
                        option_name=option_name,
                        option_values=option_values,
                        value_type_flag=value_type,
                        listener_template_option=option,
                    )
            except ValueError as exc:
                print_error(exc)
                return ReturnStatus(type=ReturnStatusType.CONTINUE)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
