from argparse import ArgumentParser

from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
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


class RedescribeAgentCommand(BaseCommand):
    name = "redescribe_agent"
    description = "Change the description of a specific agent."
    epilog = format_argparse_epilog(
        """
        Examples:
          redescribe_agent 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="Agent ID of the agent to redescribe.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="The description to assign to the agent.",
            nargs=1,
        )

    @staticmethod
    async def _redescribe_agent_by_agent_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        agent_id: str,
        description: str,
    ) -> None:
        agent = await client_rest_api_connection.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        await client_rest_api_connection.update_agent_by_agent_id(
            agent_id=agent_id,
            new_agent_attributes={"description": description},
        )
        print_success(
            f"Agent '{agent['name']}' ({agent['agent_id']}) description "
            f"updated to '{description}'",
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self._redescribe_agent_by_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=parsed_commands.agent_id[0],
                description=parsed_commands.description[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
