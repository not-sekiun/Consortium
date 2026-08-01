from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


# Stages the description of the agent generator the `create` command will build. An agent
# generator's description is display metadata rather than an agent template option, so it
# is staged here instead of through the `set` command: an agent template that declares
# its own option called `description` still sets that option through `set` as normal.
# `describe` always means "give the agent generator being created a description":
# changing the description of an agent generator that already exists is `redescribe`,
# which stays available here.
class AgentTemplateDescribeCommand(BaseConnectedCommand):
    name = "describe"
    description = (
        "Set the description to give the agent generator created from the current agent "
        "template"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          describe "Generates the long haul implants"
          describe
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "description",
            help=(
                "Description to give the created agent generator. Omit to clear a "
                "previously staged description."
            ),
            nargs="?",
            default="",
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            context.interpreter_context.agent_generator_description = (
                parsed_args.description
            )
            if not parsed_args.description:
                print_success("Cleared the staged agent generator description.")
            else:
                print_success(
                    "Created agent generators will be described as: "
                    f"'{parsed_args.description}'",
                )
        except SystemExit:
            pass

        return ContinueSignal()
