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


# Stages the description of the listener the `create` command will build. A listener's
# description is display metadata rather than a listener template option, so it is staged
# here instead of through the `set` command: a listener template that declares its own
# option called `description` still sets that option through `set` as normal. `describe`
# always means "give the listener being created a description": changing the description
# of a listener that already exists is `redescribe`, which stays available here.
class ListenerTemplateDescribeCommand(BaseConnectedCommand):
    name = "describe"
    description = (
        "Set the description to give the listener created from the current listener "
        "template"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          describe "Fronts the primary redirector"
          describe
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "description",
            help=(
                "Description to give the created listener. Omit to clear a previously "
                "staged description."
            ),
            nargs="?",
            default="",
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            context.interpreter_context.listener_description = parsed_args.description
            if not parsed_args.description:
                print_success("Cleared the staged listener description.")
            else:
                print_success(
                    "Created listeners will be described as: "
                    f"'{parsed_args.description}'",
                )
        except SystemExit:
            pass

        return ContinueSignal()
