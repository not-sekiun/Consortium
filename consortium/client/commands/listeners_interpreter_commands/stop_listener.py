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


class StopListenerCommand(BaseCommand):
    name = "stop_listener"
    description = "Stop a running listener."
    epilog = format_argparse_epilog(
        """
        Example:
            stop_listener 123e4567-e89b-12d3-a456-42661417400 # Stop a listener with listener ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="Listener ID of the listener to stop.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            client_connection = command_context.environment["client_connection"]

            # If listener does not exist, a RESTAPIError is raised and caught by the
            # outer try-except block
            listener = await client_connection.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )
            _ = await client_connection.stop_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )

            print_success(
                f'Stopped listener: "{listener["name"]}" ({listener["listener_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
