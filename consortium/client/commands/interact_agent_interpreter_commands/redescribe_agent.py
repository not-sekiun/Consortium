from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    RedescribeAgentCommand as RedescribeAgentAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class RedescribeAgentCommand(RedescribeAgentAgentsInterpreterCommand):
    name = "redescribe_agent"
    description = (
        "Change the description of a specific agent or the currently selected agent "
        "being interacted with."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          redescribe_agent "New description"  # Change the description of the currently selected agent.
          redescribe_agent 123e4567-e89b-12d3-a456-42661417400 "New description"  # Change the description of a specific agent.
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="Agent ID of the agent to redescribe.",
            nargs="?",
        )
        parser.add_argument(
            "description",
            help="The description to assign to the agent.",
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
