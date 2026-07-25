from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import (
    format_value_type_specification_epilog,
    format_value_type_specification_with_examples_epilog,
)
from consortium.client.utils.options_utils import (
    convert_option_value_strings_to_option_value,
)
from consortium.client.utils.printer_utils import print_error, print_success


class GeneratorUpdateCommand(BaseConnectedCommand):
    name = "update"
    description = (
        "Update the configuration parameters of an existing non-running agent generator"
    )
    epilog = format_value_type_specification_epilog()
    group = "Agent Generator Management Commands"
    autocompletes = Autocomplete.AGENT_GENERATOR_ID_WITH_PARAMETERS

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator to update the parameters of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_name",
            help="Name of the agent generator parameter to set the value of.",
            nargs=1,
        )
        parser.add_argument(
            "parameter_values",
            help="Value to set agent generator parameter to.",
            nargs="+",
        )
        parser.add_argument(
            "--value-type",
            "-t",
            help="Value type to use for an agent generator parameter. Applies to all values.",
            choices={"str", "int", "float", "bool"},
            nargs="?",
            default=None,
            metavar="VALUE_TYPE",
        )
        parser.add_argument(
            "--help-full",
            help=(
                "Show this help message and include detailed examples "
                "for specifying option value types."
            ),
            action="store_true",
            default=False,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            if "--help-full" in context.arguments:
                self.parser.epilog = (
                    format_value_type_specification_with_examples_epilog(
                        example_prefix="update <agent_generator_id> <parameter_name>"
                    )
                )
                self.parser.print_help()
                self.parser.epilog = self.epilog
                return ContinueSignal()

            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            agent_template_options = (
                await rest_api.get_agent_template_by_agent_template_id(
                    agent_template_id=agent_generator["creating_agent_template"][
                        "agent_template_id"
                    ],
                )
            )["options"]

            try:
                option = agent_template_options[parsed_args.parameter_name[0]]
            except KeyError:
                print_error(
                    f"Agent generator parameter not found: '{parsed_args.parameter_name[0]}'",
                )
                return ContinueSignal()

            try:
                parameter_name, parameter_value = (
                    convert_option_value_strings_to_option_value(
                        option_json_data=option,
                        value_strings=parsed_args.parameter_values,
                        value_type_flag=parsed_args.value_type,
                    )
                )
                await rest_api.update_agent_generator_by_agent_generator_id(
                    agent_generator_id=parsed_args.agent_generator_id[0],
                    new_agent_generator_attributes={
                        "parameters": {parameter_name: parameter_value},
                    },
                )
                print_success(
                    f"Updated agent generator parameter '{parameter_name}' to '{parameter_value}'",
                )
            except ValueError as exc:
                print_error(exc)
                return ContinueSignal()
        except SystemExit:
            pass

        return ContinueSignal()
