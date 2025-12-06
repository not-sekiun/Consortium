from argparse import ArgumentParser

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.options_utils import (
    convert_option_value_strings_to_option_value,
)
from consortium.client.utils.printer_utils import print_error, print_success


class SetGeneratorParameterCommand(BaseCommand):
    name = "set_generator_parameter"
    description = (
        "Modify the parameters of an existing agent generator to adjust its behavior "
        "or configuration."
    )
    epilog = format_argparse_epilog(
        """
        Note:
          By default the type of the values provided is a string. There are several
          ways to specify types for the values:

          1. The value can be explicitly annotated with a type by appending a colon
          followed by the type to the value. For example, "3:int" will be
          interpreted as the integer 3.
          2. The --value-type flag can be used to specify the type of the values. This
          will set the type of all the values to the specified type unless
          explicitly specified otherwise by their individual typing.
          3. The agent template option itself may specify the type of the values.
          This will be the default type for the values unless explicitly specified
          otherwise by their individual typing.

          The --value-type flag is set for all values of a list or dictionary value.

        Examples:
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 single_value_param 1  # No type was specified, if the option specified a type, the value will adopt that type, else it will be a string.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 single_value_param some:str:str  # If you want to include the substring :str in the value itself append :str behind it.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 single_value_param 1:int # Set the option to an integer value. This ignores the option's specified type.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 single_value_param 1 -t int # Does the same thing as the above command.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 choice_value_param 1 # If no type is specified, implicit type conversion is done for each choice. This choice will therefore match an integer 1 even if its value is a string.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 choice_value_param 1 -t int # If a type is specified, implicit type conversion is not done for each choice. Hence, the the choice contains a string "1" instead of an integer 1 it will not match.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 list_value_param 1 2 3:int  # If the list value option specifies a string type or no type at all, set the option to a list the strings 1 and 2 and an integer, 3.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 list_value_param 1 2 3 -t int   # Set the option to a list of integers 1, 2, and 3.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 list_value_param 1 2 3:str -t int   # Set the option to a list of integers 1, 2, and a string, 3. Individual type annotations will override the type set by the --value-type flag.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 dictionary_value_param key1 1 key2 2 key3 3:str -t int   # Set the option to a dictionary containing integers 1, 2, and a string, 3 to their respective keys. The keys must be strings.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param choice1 choice2 choice4  # Toggle choice1 choice2, and choice4 to True, every other choice is toggled to False. The default behaviour is to toggle choices to True.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param true:bool choice2 choice4  # Does the same thing as the above command.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param false:bool choice1 choice2 choice4  # Providing a boolean as the very first value wil toggle choice1 choice2, and choice4 to False, every other choice is toggled to True.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param true:bool  # If a single boolean is provided as the value every choice will be toggled to that value.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param t:bool  # Does the same thing as the above command.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param 1:bool  # Does the same thing as the above command.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param false -t bool  # Toggle every choice to False.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param f -t bool  # Does the same thing as the above command.
          set_generator_parameter 123e4567-e89b-12d3-a456-42661417400 toggleable_choices_value_param 0 -t bool  # Does the same thing as the above command.
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
            help="The name of the agent generator parameter to set the value of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_values",
            help="Value to set the agent generator parameter to. The number of "
            "provided values must match the expected number of values for the "
            "parameter based on the parameter's option type.",
            nargs="+",
        )
        parser.add_argument(
            "--value-type",
            "-t",
            help="Type of the agent template option to set. When set for a list or "
            "dictionary value type option, all the elements of the list or values "
            "of the dictionary will be set to that same type unless explicitly "
            "specified as otherwise by their individual typing.",
            choices={"str", "int", "float", "bool"},
            nargs="?",
            default=None,
            metavar="VALUE_TYPE",
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            agent_generator = await client_rest_api_connection.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            try:
                agent_template_options = (
                    await client_rest_api_connection.get_agent_template_by_agent_template_id(
                        agent_template_id=agent_generator["creating_agent_template"][
                            "agent_template_id"
                        ],
                    )
                )["options"]
            except KeyError:
                print_error(
                    f"Agent template for agent generator '{agent_generator['name']}' "
                    f"({agent_generator['agent_generator_id']}) not found",
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            try:
                option = agent_template_options[parsed_args.parameter_name[0]]
            except KeyError:
                print_error(
                    f"Agent generator parameter '{parsed_args.parameter_name[0]}' does not "
                    f"exist",
                )
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            try:
                parameter_name, parameter_value = (
                    convert_option_value_strings_to_option_value(
                        option_json_data=option,
                        value_strings=parsed_args.parameter_values,
                        value_type_flag=parsed_args.value_type,
                    )
                )
                await client_rest_api_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: parameter_value},
                    },
                )
                print_success(
                    f"Set agent generator parameter '{parameter_name}' to {parameter_value!r}",
                )
            except ValueError as exc:
                print_error(exc)
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
