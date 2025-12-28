from argparse import ArgumentParser

from consortium.client.client_rest_api import RestAPI
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


class AgentRenameCommand(BaseCommand):
    name = "rename"
    description = "Set the name of an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to rename.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="New name to assign to the agent.",
            nargs=1,
        )

    @staticmethod
    async def _rename_agent(
        rest_api: RestAPI,
        agent_id: str,
        new_name: str,
    ) -> None:
        agent = await rest_api.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        await rest_api.update_agent_by_agent_id(
            agent_id=agent_id,
            new_agent_attributes={"name": new_name},
        )
        print_success(
            f"Renamed agent '{agent['name']}' ({agent['agent_id']}) to '{new_name}'"
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._rename_agent(
                rest_api=rest_api,
                agent_id=parsed_commands.agent_id[0],
                new_name=parsed_commands.name[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
