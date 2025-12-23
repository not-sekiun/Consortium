from argparse import ArgumentParser

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class LaunchListenerCommand(BaseCommand):
    name = "launch_listener"
    description = (
        "Create a listener with the currently set listener template options and then "
        "also start the created listener."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          launch_listener
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        pass

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            listener_template_id = command_context.environment["listener_template"][
                "listener_template_id"
            ]
            listener_template_options = command_context.environment[
                "listener_template"
            ]["options"]

            listener_template_option_values = {}
            for option_name, option in listener_template_options.items():
                listener_template_option_values[option_name] = option["value"]
            listener = await client_rest_api_connection.create_listener_through_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
                listener_template_option_values=listener_template_option_values,
            )

            _ = await client_rest_api_connection.start_listener_by_listener_id(
                listener_id=listener["listener_id"],
            )

            print_success(
                f"Created and started listener: '{listener['name']}' ({listener['listener_id']})",
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
