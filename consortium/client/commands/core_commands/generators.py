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


class GeneratorsCommand(BaseCommand):
    name = "generators"
    description = (
        "Switch to the generators interpreter, the interface for creating and managing "
        "the generation of agent payloads."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          generators
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            print_info("Switching to the generators interpreter...")
            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.GENERATORS_INTERPRETER},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
