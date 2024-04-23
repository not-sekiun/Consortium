import json
from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import print_success
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class CreateListenerCommand(BaseCommand):
    name = "create_listener"
    description = "Create a listener with the currently set listener template options."
    epilog = argparse_epilog_formatter(
        """
        Example:
            create_listener  # Create a listener with the currently set listener template options
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        pass

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)

            listener_template_id = command_context.environment["listener_template_id"]
            listener_template_options = command_context.environment[
                "listener_template"
            ]["options"]
            client_connection = command_context.environment["client_connection"]

            listener_template_option_values = {}
            for option_name, option in listener_template_options.items():
                listener_template_option_values[option_name] = option["value"]

            listener = await client_connection.create_listener_through_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
                listener_template_option_values=listener_template_option_values,
            )

            print_success(
                f'Created listener: "{listener["name"]}" ({listener["listener_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
