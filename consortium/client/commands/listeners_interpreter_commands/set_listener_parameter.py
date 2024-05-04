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
from consortium.client.utils.printer_utils import print_success


class SetListenerParameterCommand(BaseCommand):
    name = "set_listener_parameter"
    description = "Change the parameter of an already created listener."
    epilog = format_argparse_epilog(
        """
        Example:
            set_listener_parameter 123e4567-e89b-12d3-a456-42661417400 parameter value  # Set the parameter named "parameter" to the value "value" for the listener with listener ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to change the parameters of.",
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
            help="Type of the listener parameter to set.",
            choices=["str", "int", "float", "bool", "list", "dict"],
            nargs=1,
            default=["str"],  # nargs=1 sets the value to be a list with one element.
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            listener = await client_connection.get_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )

            # TODO: Do data type processing based on the listener template. Also
            #  associate the listener template with the listener.
            parameter_value = parsed_args.parameter_value
            await client_connection.update_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
                new_listener_attributes={
                    "parameters": {parsed_args.parameter_name[0]: parameter_value[0]},
                },
            )
            print_success(
                f'Set parameter "{parsed_args.parameter_name[0]}" to '
                f'"{parameter_value[0]}" for listener: {listener["name"]} '
                f'({listener["listener_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
