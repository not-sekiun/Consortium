from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.agent_generator_command_utils import (
    display_all_agent_generators,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class GeneratorListCommand(BaseConnectedCommand):
    name = "list"
    description = "List all agent generators along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Agent Generator Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            display_all_agent_generators(
                all_agent_generators=await rest_api.get_all_agent_generators()
            )
        except SystemExit:
            pass

        return ContinueSignal()
