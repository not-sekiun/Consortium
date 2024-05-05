from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class RenameListenerCommand(BaseCommand):
    name = "rename_listener"
    description = (
        "Change the name of a listener instance without altering its configured "
        "parameters."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            rename_listener 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to rename.",
            nargs=1,
        )
        parser.add_argument(
            "new_name",
            help="New name to assign to the listener.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]

            await client_connection.update_listener_by_listener_id(
                listener_id=parsed_commands.listener_id[0],
                new_listener_attributes={"name": parsed_commands.new_name[0]},
            )

            print_success(
                f'Listener renamed to "{parsed_commands.new_name[0]}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
