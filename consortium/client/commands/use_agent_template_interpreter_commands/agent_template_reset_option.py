import copy
from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success


class AgentTemplateResetOptionCommand(BaseCommand[ConnectedContext]):
    name = "reset"
    description = "Reset the current agent template's option to its default value"
    epilog = format_argparse_epilog(
        """
        Examples:
          reset option_name
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "option_name",
            help="Name of the agent template option to reset.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            agent_template_options = context.interpreter_context.agent_template[
                "options"
            ]
            option_name = parsed_args.option_name[0]

            try:
                option = agent_template_options[option_name]
            except KeyError:
                print_error(
                    f"Agent template option not found: '{option_name}'",
                )
                return ContinueSignal()

            option["value"] = copy.deepcopy(option["default_value"])
            print_success(
                f"Reset agent template option '{option_name}' to its default value '{option['value']}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
