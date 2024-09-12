from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class HomeCommand(BaseCommand):
    name = "home"
    description = (
        "Return to the home interpreter, the main control interface of the Consortium "
        "framework."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          home
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            print_info("Switching to the home interpreter...")
            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.HOME_INTERPRETER},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
