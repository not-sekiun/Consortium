from consortium.client.models.return_status_models import (
    InterpreterType,
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
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
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the listeners interpreter...")
            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.LISTENERS_INTERPRETER},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
