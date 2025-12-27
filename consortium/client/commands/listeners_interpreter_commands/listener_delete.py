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


class ListenerDeleteCommand(BaseCommand):
    name = "delete"
    description = "Delete a non-running listener by its listener ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          delete 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to delete.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If listener does not exist, a RESTAPIError is raised and caught by the
            # outer try-except block
            listener = await rest_api.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )
            _ = await rest_api.delete_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )
            print_success(
                f"Deleted listener '{listener['name']}' ({listener['listener_id']})",
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
