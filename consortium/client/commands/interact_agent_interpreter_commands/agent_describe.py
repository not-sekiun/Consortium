from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentDescribeCommand as AgentDescribeAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentDescribeCommand(AgentDescribeAgentsInterpreterCommand):
    name = "ag-desc"
    description = (
        "Set the description of the current agent, or a specific agent by its agent ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          ag-desc "New description"
          ag-desc 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent whose description should be changed (defaults to the "
                "current agent being interacted with if not provided)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "description",
            help="New description for the agent.",
            nargs=1,
        )

    async def run_command(self, command_context: CommandContext) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self._redescribe_agent_by_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=parsed_commands.agent_id
                if parsed_commands.agent_id
                else command_context.environment["agent"]["agent_id"],
                description=parsed_commands.description[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
