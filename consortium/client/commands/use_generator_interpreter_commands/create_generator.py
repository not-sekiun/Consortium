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


class CreateGeneratorCommand(BaseCommand):
    name = "create_generator"
    description = "Create an agent generator with the currently set agent generator template options."
    epilog = argparse_epilog_formatter(
        """
        Example:
            create_generator  # Create a listener with the currently set listener template options
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        pass

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)

            agent_template_id = command_context.environment["agent_template_id"]
            agent_template_options = command_context.environment["agent_template"][
                "options"
            ]
            client_connection = command_context.environment["client_connection"]

            agent_template_option_values = {}
            for option_name, option in agent_template_options.items():
                agent_template_option_values[option_name] = option["value"]

            agent_generator = await client_connection.create_agent_generator_through_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
                agent_template_option_values=agent_template_option_values,
            )

            print_success(
                f'Created agent generator: "{agent_generator["name"]}" ({agent_generator["agent_generator_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
