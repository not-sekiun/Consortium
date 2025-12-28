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


class DeleteGeneratorCommand(BaseCommand):
    name = "delete_generator"
    description = "Delete a non-running agent generator."
    epilog = format_argparse_epilog(
        """
        Examples:
          delete_generator 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="Agent generator ID of the non-running agent generator to delete.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.client_session.rest_api
            # If agent generator does not exist, a RESTAPIError is raised and caught by
            # the outer try-except block
            agent_generator = await client_rest_api_connection.get_agent_generator_by_agent_generator_id(
                parsed_args.agent_generator_id[0],
            )

            _ = await client_rest_api_connection.delete_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )

            print_success(
                f'Deleted agent generator: "{agent_generator["name"]}" '
                f"({agent_generator['agent_generator_id']})",
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
