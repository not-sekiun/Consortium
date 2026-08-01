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


# Stages the name of the agent generator the `create` command will build. An agent
# generator's name is display metadata rather than an agent template option, so it is
# staged here instead of through the `set` command: an agent template that declares its
# own option called `name` still sets that option through `set` as normal. This command
# is deliberately called `name` rather than `rename`: nothing exists to be renamed yet,
# and `rename` is left free to keep meaning what it means everywhere else, renaming an
# agent generator that has already been created.
class AgentTemplateNameCommand(BaseConnectedCommand):
    name = "name"
    description = (
        "Set the name to give the agent generator created from the current agent "
        "template"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          name "My agent generator"
          name
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "name",
            help=(
                "Name to give the created agent generator. Omit to clear a previously "
                "staged name and have a random one generated on creation instead."
            ),
            nargs="?",
            default=None,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            context.interpreter_context.agent_generator_name = parsed_args.name
            if parsed_args.name is None:
                print_success(
                    "Cleared the staged agent generator name. A random name will be "
                    "generated on creation.",
                )
            else:
                print_success(
                    f"Created agent generators will be named: '{parsed_args.name}'",
                )
        except SystemExit:
            pass

        return ContinueSignal()
