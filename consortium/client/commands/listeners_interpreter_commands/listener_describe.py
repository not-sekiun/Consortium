from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


# Paired with `rename`: both act on a listener that already exists. Giving a description
# to a listener that has yet to be created is done through the `create` command's
# -d/--description flag inside a listener template's context.
class ListenerDescribeCommand(BaseConnectedCommand):
    name = "describe"
    description = "Set the description of a listener by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          describe 123e4567-e89b-12d3-a456-426614174000 "New description"
        """,
    )
    group = "Listener Management Commands"
    autocompletes = Autocomplete.LISTENER_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener whose description should be changed.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="New description for the listener.",
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
                new_listener_attributes={
                    "description": parsed_args.description[0],
                },
            )
            print_success(
                f"Updated description of listener '{listener['name']}' ({listener['listener_id']}) "
                f"to '{parsed_args.description[0]}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
