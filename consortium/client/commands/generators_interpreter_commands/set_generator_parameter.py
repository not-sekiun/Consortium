from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success


class SetGeneratorParameterCommand(BaseCommand):
    name = "set_generator_parameter"
    description = (
        "Modify the parameters of an existing agent generator to adjust its behavior "
        "or configuration."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 parameter value
            set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 parameter 1 -t int  # Explicitly specify the parameter type.
            set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 float_parameter 3.14  # If the type of the parameter is specified by the agent generator's corresponding agent template, the type will be inferred.
            set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 parameter "['value1', 'value2']"  # A list parameter is set as a JSON string so it must be escaped.
            set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 parameter "{'key1': 'value1', 'key2': 'value2'}"  # A dictionary parameter is set as a JSON string so it must be escaped.
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help=(
                "Agent generator ID of the agent generator to change the parameters of."
            ),
            nargs=1,
        )
        parser.add_argument(
            "parameter_name",
            help="The name of the parameter to change the value of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_value",
            help="The value to set the parameter to.",
            nargs=1,
        )
        parser.add_argument(
            "--parameter-type",
            "-t",
            help="Type of the agent generator parameter to set.",
            choices=["str", "int", "float", "bool", "list", "dict"],
            nargs=1,
            default=["str"],  # nargs=1 sets the value to be a list with one element.
        )

    async def _handle_single_value_option(self): ...

    async def _handle_list_value_option(self): ...

    async def _handle_choice_value_option(self): ...

    async def _handle_dictionary_value_option(self): ...

    async def _handle_toggleable_choices_value_option(self): ...

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            agent_generator = (
                await client_connection.get_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                )
            )
            try:
                option = agent_generator["options"][parsed_args.parameter_name[0]]
            except KeyError:
                print_error(
                    f'Parameter "{parsed_args.parameter_name[0]}" does not exist in '
                    f'agent generator: "{agent_generator["name"]}" '
                    f'({agent_generator["agent_generator_id"]})',
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
            option_type_str_enum_to_handler_function_map = {
                "SINGLE_VALUE_OPTION": self._handle_single_value_option,
                "LIST_VALUE_OPTION": self._handle_list_value_option,
                "CHOICE_VALUE_OPTION": self._handle_choice_value_option,
                "DICTIONARY_VALUE_OPTION": self._handle_dictionary_value_option,
                "TOGGLEABLE_CHOICES_VALUE_OPTION": self._handle_toggleable_choices_value_option,
            }

            # TODO: Do data type processing based on the agent template. Also
            #  associate the agent template with the agent generator.
            option_type_str_enum_to_handler_function_map[option["type"]]()

            parameter_value = parsed_args.parameter_value
            await client_connection.update_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
                new_agent_generator_attributes={
                    "parameters": {parsed_args.parameter_name[0]: parameter_value[0]},
                },
            )
            print_success(
                f'Set parameter "{parsed_args.parameter_name[0]}" to '
                f'"{parameter_value[0]}" for agent generator: '
                f'"{agent_generator["name"]}" '
                f'({agent_generator["agent_generator_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
