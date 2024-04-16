from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.utils.printer_utils import print_info
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class ListenersCommand(BaseCommand):
    name = "listeners"
    description = "Switch to the listeners interpreter."
    epilog = argparse_epilog_formatter(
        """
        Examples:
            listeners  # Switch to the listeners interpreter.
        """,
    )

    def configure_parser(self, parser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            print_info("Switching to the listeners interpreter...")
            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.LISTENERS},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
