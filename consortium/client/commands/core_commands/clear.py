import platform
import subprocess

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error


class ClearCommand(BaseCommand):
    name = "clear"
    description = "Clear the terminal screen."
    epilog = format_argparse_epilog(
        """
        Examples:
            clear
        """,
    )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            if platform.system() == "Windows":
                subprocess.run("cls", shell=True)
            # platform.system() returns "Darwin" for macOS and "Linux" for nix systems.
            elif platform.system() in ["Darwin", "Linux"]:
                subprocess.run("clear", shell=True)
            else:
                print_error(
                    "Cannot clear terminal screen on unsupported operating system.",
                )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
