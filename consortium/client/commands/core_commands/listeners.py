from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchListenersInterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class ListenersCommand(BaseCommand):
    name = "listeners"
    description = "Switch to the listeners interpreter context to manage listeners"
    epilog = format_argparse_epilog(
        """
        Examples:
          listeners
        """,
    )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the listeners interpreter...")
            return SwitchListenersInterpreterSignal()
        except SystemExit:
            pass

        return ContinueSignal()
