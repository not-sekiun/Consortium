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


class AgentsCommand(BaseCommand):
    name = "agents"
    description = "Switch to the agents interpreter context to manage agents"
    epilog = format_argparse_epilog(
        """
        Examples:
          agents
        """,
    )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            print_info("Switching to the agents interpreter...")
            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={"interpreter_type": InterpreterType.AGENTS_INTERPRETER},
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
