import platform
import subprocess

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error


class ClearCommand(BaseCommand):
    name = "clear"
    description = "Clear the terminal screen"
    epilog = format_argparse_epilog(
        """
        Examples:
          clear
        """,
    )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            if platform.system() == "Windows":
                subprocess.run("cls", shell=True)
            # platform.system() returns "Darwin" for macOS and "Linux" for nix systems.
            elif platform.system() in ["Darwin", "Linux"]:
                subprocess.run("clear", shell=True)
            else:
                print_error(
                    "Cannot clear terminal screen on unsupported operating system",
                )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
