from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.listener_command_utils import display_all_listeners


class ListenerListCommand(BaseConnectedCommand):
    name = "list"
    description = "List all listeners along with their essential information"
    epilog = format_argparse_epilog(
        """
        Examples:
          list
        """,
    )
    group = "Listener Management Commands"

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            display_all_listeners(all_listeners=await rest_api.get_all_listeners())
        except SystemExit:
            pass

        return ContinueSignal()
