from argparse import ArgumentParser

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ListenerRenameCommand(BaseCommand):
    name = "rename"
    description = "Set the name of a listener by its listener ID"
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
            "new_name",
            help="New name to assign to the listener.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            listener = await rest_api.get_listener_by_listener_id(
                listener_id=parsed_commands.listener_id[0],
            )
            await rest_api.update_listener_by_listener_id(
                listener_id=parsed_commands.listener_id[0],
                new_listener_attributes={"name": parsed_commands.new_name[0]},
            )
            print_success(
                f"Renamed listener '{listener['name']}' ({listener['listener_id']}) "
                f"to '{parsed_commands.new_name[0]}'",
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
