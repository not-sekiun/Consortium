from argparse import ArgumentParser

from consortium.client.client_rest_api import RestApi
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


class AgentDescribeCommand(BaseCommand):
    name = "describe"
    description = "Set the description of an agent by its agent ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          describe 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent whose description should be changed.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="New description for the agent.",
            nargs=1,
        )

    @staticmethod
    async def _redescribe_agent_by_agent_id(
        rest_api: RestApi,
        agent_id: str,
        description: str,
    ) -> None:
        agent = await rest_api.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        await rest_api.update_agent_by_agent_id(
            agent_id=agent_id,
            new_agent_attributes={"description": description},
        )
        print_success(
            f"Agent '{agent['name']}' ({agent['agent_id']}) description "
            f"updated to '{description}'",
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._redescribe_agent_by_agent_id(
                rest_api=rest_api,
                agent_id=parsed_commands.agent_id[0],
                description=parsed_commands.description[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
