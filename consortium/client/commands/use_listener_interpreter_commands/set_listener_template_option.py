import json
from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import print_error, print_success
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class SetListenerTemplateOptionCommand(BaseCommand):
    name = "set_listener_template_option"
    description = "Set a listener template option to a specific value."
    epilog = argparse_epilog_formatter(
        """
        Example:
            set_listener_template_option local_host 0.0.0.0  # All values are treated as strings by default.
            set_listener_template_option local_port 1337 -t int  # Explicitly set the type of the set value to an integer.
            set_listener_template_option list_option '["str_value_1",1,3.14,True]' -t list  # For values that expect lists set the type to "list" and escape the value with quotes.
            set_listener_template_option dict_option '{"key1":"str_value_1","key2":1,"key3":3.14,"key4":True}' -t dict  # For values that expect dictionaries set the type to "dict" and escape the value with quotes.
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Listener template option name of the listener template option to set.",
            nargs=1,
        )
        parser.add_argument(
            "option_value",
            help="Value to set the listener template option to.",
            nargs=1,
        )
        parser.add_argument(
            "--value-type",
            "-t",
            help="Type of the listener template option to set.",
            choices=["str", "int", "float", "bool", "list", "dict"],
            nargs=1,
            default=["str"],  # nargs=1 sets the value to be a list with one element.
        )

    @staticmethod
    def _convert_value_type(
        value: str,
        value_type: str,
    ) -> str | int | float | bool | list | dict:
        if value_type not in ("str", "int", "float", "bool", "list", "dict"):
            raise ValueError(
                f'Value type "{value_type}" is not a valid value type.',
            )

        try:
            if value_type == "str":
                return value
            elif value_type == "int":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "bool":
                return bool(value)
            elif value_type == "list":
                value = json.loads(value)
                if not isinstance(value, list):
                    raise ValueError
                for element in value:
                    if not isinstance(element, (str, int, float, bool)):
                        raise ValueError
                return value
            elif value_type == "dict":
                value = json.loads(value)
                if not isinstance(value, dict):
                    raise ValueError
                for key, value in value.items():
                    if not isinstance(key, str):
                        raise ValueError
                return value
        except (json.JSONDecodeError, ValueError):
            raise ValueError(
                f'Value "{value}" could not be converted to "{value_type}" type data.',
            )

    def _handle_single_value_option(
        self,
        option_name: str,
        option_value: str,
        listener_template_options: dict,
    ) -> None:
        # value_type can only be one of str, int, float, bool. If value_type is
        # specified we automatically attempt to convert the string value to the
        # specified type.
        if listener_template_options[option_name]["value_type"]:
            try:
                option_value = self._convert_value_type(
                    value=option_value,
                    value_type=listener_template_options[option_name]["value_type"],
                )
            except ValueError as exc:
                print_error(exc)
                return

        listener_template_options[option_name]["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to "{listener_template_options[option_name]["value"]}"',
        )

    def _handle_choice_value_option(
        self,
        option_name: str,
        option_value: str,
        listener_template_options: dict,
    ) -> None:
        choice_and_choice_types_tuple_list = [
            [value, type(value).__name__]
            for value in listener_template_options[option_name]["available_values"]
        ]

        matched_choice = False
        # For each choice, try to convert the option_value to the choice's type, then
        # perform a comparison to check if the provided option was that choice.
        for choice, choice_type in choice_and_choice_types_tuple_list:
            try:
                option_value = self._convert_value_type(
                    value=option_value,
                    value_type=choice_type,
                )
                if option_value == choice:
                    matched_choice = True
                    break
            except ValueError:
                pass

        if not matched_choice:
            print_error(
                f'Value "{option_value}" is not in the available values for option "{option_name}"',
            )
            return

        listener_template_options[option_name]["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to "{listener_template_options[option_name]["value"]}"',
        )

    def _handle_list_value_option(
        self,
        option_name: str,
        option_value: str,
        listener_template_options: dict,
    ) -> None:
        try:
            option_value = self._convert_value_type(
                value=option_value,
                value_type="list",
            )
        except ValueError as exc:
            print_error(exc)
            return

        # value_type can only be one of str, int, float, bool. If value_type is
        # specified we automatically attempt to convert the value of each element within
        # the list to the specified type.
        if listener_template_options[option_name]["value_type"]:
            try:
                option_value = [
                    self._convert_value_type(
                        value=element,
                        value_type=listener_template_options[option_name]["value_type"],
                    )
                    for element in option_value
                ]
            except ValueError as exc:
                print_error(exc)
                return

        listener_template_options[option_name]["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to "{listener_template_options[option_name]["value"]}"',
        )

    def _handle_dictionary_value_option(
        self,
        option_name: str,
        option_value: str,
        listener_template_options: dict,
    ) -> None:
        try:
            option_value = self._convert_value_type(
                value=option_value,
                value_type="dict",
            )
        except ValueError as exc:
            print_error(exc)
            return

        # value_type can only be one of str, int, float, bool. If value_type is
        # specified we automatically attempt to convert the value of each element within
        # the dict to the specified type.
        if listener_template_options[option_name]["value_type"]:
            try:
                option_value = {
                    key: self._convert_value_type(
                        value=value,
                        value_type=listener_template_options[option_name]["value_type"],
                    )
                    for key, value in option_value.items()
                }
            except ValueError as exc:
                print_error(exc)
                return

        listener_template_options[option_name]["value"] = option_value
        print_success(
            f'Set listener template option "{option_name}" to "{listener_template_options[option_name]["value"]}"',
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            listener_template_options = command_context.environment[
                "listener_template"
            ]["options"]
            option_name = parsed_args.option_name[0]
            option_value = parsed_args.option_value[0]
            value_type = parsed_args.value_type[0]
            option_type = listener_template_options[option_name]["option_type"]
            option_type_str_to_handler_map = {
                "SINGLE_VALUE_OPTION": self._handle_single_value_option,
                "CHOICE_VALUE_OPTION": self._handle_choice_value_option,
                "LIST_VALUE_OPTION": self._handle_list_value_option,
                "DICTIONARY_VALUE_OPTION": self._handle_dictionary_value_option,
            }

            try:
                option_value = self._convert_value_type(
                    value=option_value,
                    value_type=value_type,
                )
            except ValueError as exc:
                print_error(exc)
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            option_type_str_to_handler_map[option_type](
                option_name=option_name,
                option_value=option_value,
                listener_template_options=listener_template_options,
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
