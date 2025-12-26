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
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the home interpreter...")
            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.HOME_INTERPRETER},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
