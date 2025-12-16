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


class RenameAgentCommand(BaseCommand):
    name = "rename_agent"
    description = "Change the name of a specific agent."
    epilog = format_argparse_epilog(
        """
        Examples:
          rename_agent 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="Agent ID of the agent to rename.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="The name to assign to the agent.",
            nargs=1,
        )

    @staticmethod
    async def _rename_agent_by_agent_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        agent_id: str,
        new_name: str,
    ) -> None:
        agent = await client_rest_api_connection.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        await client_rest_api_connection.update_agent_by_agent_id(
            agent_id=agent_id,
            new_agent_attributes={"name": new_name},
        )
        print_success(
            f"Agent '{agent['name']}' ({agent['agent_id']}) renamed to '{new_name}'",
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self._rename_agent_by_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=parsed_commands.agent_id[0],
                new_name=parsed_commands.name[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
