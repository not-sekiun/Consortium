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
from consortium.client.utils.options_utils import (
    convert_option_value_strings_to_option_value,
)
from consortium.client.utils.printer_utils import print_error, print_success


class ListenerUpdateCommand(BaseCommand):
    name = "update"
    description = (
        "Update the configuration parameters of an existing non-running listener"
    )
    epilog = format_set_value_command_epilog(command_name="update")
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to update the parameters of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_name",
            help="Name of the listener parameter to set the value of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_values",
            help="Value to set the listener parameter to. The number of provided "
            "values must match the expected number of values for the parameter "
            "based on the parameter's option type.",
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

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            listener = await rest_api.get_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )

            try:
                listener_template_options = (
                    await rest_api.get_listener_template_by_listener_template_id(
                        listener_template_id=listener["creating_listener_template"][
                            "listener_template_id"
                        ],
                    )
                )["options"]
            except KeyError:
                print_error(
                    f"Listener template for listener '{listener['name']}' "
                    f"({listener['listener_id']}) was not found",
                )
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            try:
                option = listener_template_options[parsed_args.parameter_name[0]]
            except KeyError:
                print_error(
                    f"Listener parameter with name '{parsed_args.parameter_name[0]}' was not found",
                )
                return ReturnStatus(type=ReturnStatusType.CONTINUE)

            try:
                parameter_name, parameter_value = (
                    convert_option_value_strings_to_option_value(
                        option_json_data=option,
                        value_strings=parsed_args.parameter_values,
                        value_type_flag=parsed_args.value_type,
                    )
                )
                await rest_api.update_listener_by_listener_id(
                    listener_id=parsed_args.listener_id[0],
                    new_listener_attributes={
                        "parameters": {parameter_name: parameter_value},
                    },
                )
                print_success(
                    f"Updated listener parameter '{parameter_name}' to '{parameter_value}'",
                )
            except ValueError as exc:
                print_error(exc)
                return ReturnStatus(type=ReturnStatusType.CONTINUE)
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
