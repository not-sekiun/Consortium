from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ListenerCancelCommand(BaseCommand):
    name = "cancel"
    description = "Forcefully cancel the execution of a running listener by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          cancel 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to cancel.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If listener does not exist, a RESTAPIError is raised and caught by the
            # outer try-except block
            listener = await rest_api.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )
            _ = await rest_api.cancel_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )
            print_success(
                f"Cancelled listener: '{listener['name']}' ({listener['listener_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
