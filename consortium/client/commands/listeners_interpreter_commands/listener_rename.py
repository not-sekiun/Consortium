from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ListenerRenameCommand(BaseConnectedCommand):
    name = "rename"
    description = "Set the name of a listener by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to rename.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="New name to assign to the listener.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            listener = await rest_api.get_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )
            await rest_api.update_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
                new_listener_attributes={"name": parsed_args.name[0]},
            )
            print_success(
                f"Renamed listener '{listener['name']}' ({listener['listener_id']}) "
                f"to '{parsed_args.name[0]}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
