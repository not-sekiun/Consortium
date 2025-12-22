from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    InfoAgentCommand as InfoAgentAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class InfoAgentCommand(InfoAgentAgentsInterpreterCommand):
    name = "info_agent"
    description = (
        "Display detailed information about a specific agent or for the currently "
        "selected agent being interacted with."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info_agent  # Display detailed information about the currently selected agent.
          info_agent 123e4567-e89b-12d3-a456-42661417400  # Display detailed information about a specific agent.
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to display detailed information for.",
            nargs="?",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self.display_agent_info_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id
                else command_context.environment["agent"]["agent_id"],
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
