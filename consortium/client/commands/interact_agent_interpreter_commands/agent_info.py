from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentInfoCommand as InfoAgentAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentInfoCommand(InfoAgentAgentsInterpreterCommand):
    name = "ag-info"
    description = (
        "Display information about the current agent, or a specific agent by its agent "
        "ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          ag-info
          ag-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to display information for (defaults to the current "
                "agent being interacted with if not provided)."
            ),
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
            if parsed_args.agent_id is not None:
                agent = await client_rest_api_connection.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id[0]
                )
            else:
                agent = command_context.environment["agent"]
            self._display_agent_info(agent=agent)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
