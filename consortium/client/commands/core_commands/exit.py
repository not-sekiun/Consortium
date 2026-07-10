import consortium.client.client_singletons as client_singletons
from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    ExitClientSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import print_error, print_info, print_success

client_sessions_service = client_singletons.client_sessions_service


class ExitCommand(BaseCommand[AnyContext]):
    name = "exit"
    description = "Exit the Consortium client"
    epilog = format_argparse_epilog(
        """
        Examples:
          exit
        """,
    )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)

            print_info("Disconnecting all client sessions...")
            for client_session in client_sessions_service.get_all_client_sessions():
                if not client_session.connected:
                    continue

                try:
                    await client_session.disconnect()
                    print_success(
                        f"Disconnected client session {client_session}",
                    )
                except Exception as exc:
                    print_error(
                        f"Error disconnecting client session {client_session}.", exc=exc
                    )

            print_info("Exiting...")
            return ExitClientSignal()
        except SystemExit:
            pass

        return ContinueSignal()
