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


class CancelGeneratorCommand(BaseCommand):
    name = "cancel_generator"
    description = "Cancel a running agent generator."
    epilog = format_argparse_epilog(
        """
        Example:
            cancel_generator 123e4567-e89b-12d3-a456-42661417400 # Cancel an agent generator with agent generator ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="Agent generator ID of the agent generator to cancel.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            client_connection = command_context.environment["client_connection"]

            # If agent generator does not exist, a RESTAPIError is raised and caught by
            # the outer try-except block
            agent_generator = (
                await client_connection.get_agent_generator_by_agent_generator_id(
                    parsed_args.agent_generator_id[0],
                )
            )
            _ = await client_connection.cancel_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )

            print_success(
                f'Cancelled agent generator: "{agent_generator["name"]}" '
                f'({agent_generator["agent_generator_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
