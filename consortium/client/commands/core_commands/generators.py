from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchGeneratorsInterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class GeneratorsCommand(BaseCommand[AnyContext]):
    name = "generators"
    description = "Switch to the generators interpreter context to manage generators"
    epilog = format_argparse_epilog(
        """
        Examples:
          generators
        """,
    )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the generators interpreter...")
            return SwitchGeneratorsInterpreterSignal()
        except SystemExit:
            pass

        return ContinueSignal()
