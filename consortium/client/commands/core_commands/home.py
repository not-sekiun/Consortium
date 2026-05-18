from consortium.client.models.context_model import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchHomeInterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class HomeCommand(BaseCommand):
    name = "home"
    description = "Switch to the home interpreter to manage client sessions"
    epilog = format_argparse_epilog(
        """
        Examples:
          home
        """,
    )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the home interpreter...")
            return SwitchHomeInterpreterSignal()
        except SystemExit:
            pass

        return ContinueSignal()
