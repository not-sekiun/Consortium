from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchAgentsInterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class AgentsCommand(BaseCommand[AnyContext]):
    name = "agents"
    description = "Switch to the agents interpreter context to manage agents"
    epilog = format_argparse_epilog(
        """
        Examples:
          agents
        """,
    )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the agents interpreter...")
            return SwitchAgentsInterpreterSignal()
        except SystemExit:
            pass

        return ContinueSignal()
