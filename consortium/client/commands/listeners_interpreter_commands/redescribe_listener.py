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


class RedescribeListenerCommand(BaseCommand):
    name = "redescribe_listener"
    description = (
        "Update the description of a listener instance for better organization and "
        "identification."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          redescribe_listener 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to redescribe.",
            nargs=1,
        )
        parser.add_argument(
            "new_description",
            help="New description to assign to the listener.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            listener = await client_connection.get_listener_by_listener_id(
                listener_id=parsed_commands.listener_id[0],
            )

            await client_connection.update_listener_by_listener_id(
                listener_id=parsed_commands.listener_id[0],
                new_listener_attributes={
                    "description": parsed_commands.new_description[0],
                },
            )

            print_success(
                f"Listener {listener["name"]} ({listener["listener_id"]}) description "
                f'updated to: "{parsed_commands.new_description[0]}"',
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
