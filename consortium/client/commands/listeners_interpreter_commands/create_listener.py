from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter

client_connections_service = client_singletons.client_connections_service


class CreateListenerCommand(BaseCommand):
    name = "create_listener"
    description = "Create a listener."
    epilog = argparse_epilog_formatter(
        """
        Example:
            create_listener 123e4567-e89b-12d3-a456-42661417400  # Create a listener using the listener template with listener template ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener to create.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            listener_template = await command_context.environment[
                "client_connection"
            ].get_listener_template_by_listener_template_id(
                parsed_args.listener_template_id[0],
            )

            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data=listener_template["listener_template_id"],
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
