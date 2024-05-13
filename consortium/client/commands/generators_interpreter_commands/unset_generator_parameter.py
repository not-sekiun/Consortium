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


class UnsetGeneratorParameterCommand(BaseCommand):
    name = "unset_generator_parameter"
    description = (
        "Unset an agent generator parameter for a specified agent generator to adjust "
        "its behavior or configuration."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            unset_generator_parameter 123e4567-e89b-12d3-a456-42661417400 option_name
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="Agent generator ID of the agent generator to unset the parameters of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_name",
            help="The name of the agent generator parameter to unset the value of.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            agent_template_options = command_context.environment["agent_template"][
                "options"
            ]
            parameter_name = parsed_args.parameter_name[0]

            try:
                option = agent_template_options[parameter_name]
            except KeyError:
                print_error(
                    f"Parameter '{parameter_name}' does not exist in the agent generator.",
                )
                return ReturnStatus(ClientReturnStatusType.CONTINUE)

            if option["option_type"] == "LIST_VALUE_OPTION":
                await client_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: []},
                    },
                )
                print_success(
                    f'Option "{parameter_name}" has been unset.',
                )
            elif option["option_type"] == "DICTIONARY_VALUE_OPTION":
                await client_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: {}},
                    },
                )
                print_success(
                    f'Option "{parameter_name}" has been unset.',
                )
            elif option["option_type"] == "TOGGLEABLE_CHOICES_VALUE_OPTION":
                print_error(
                    f'Option "{parameter_name}" is of option type '
                    f'"{option["option_type"]}" and cannot be unset.',
                )
            # SINGLE_VALUE_OPTION and CHOICE_VALUE_OPTION
            else:
                await client_connection.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: None},
                    },
                )
                print_success(
                    f'Option "{parameter_name}" has been unset.',
                )
        except SystemExit:
            pass

        return ReturnStatus(ClientReturnStatusType.CONTINUE)
