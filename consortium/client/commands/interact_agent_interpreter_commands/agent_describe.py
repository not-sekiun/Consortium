from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentDescribeCommand as AgentDescribeAgentsInterpreterCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentDescribeCommand(AgentDescribeAgentsInterpreterCommand):
    name = "describe"
    description = (
        "Set the description of the current agent, or a specific agent by its agent ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          desc "New description"
          desc 123e4567-e89b-12d3-a456-42661417400 "New description"
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

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._redescribe_agent_by_agent_id(
                rest_api=rest_api,
                agent_id=parsed_commands.agent_id
                if parsed_commands.agent_id
                else context.environment["agent"]["agent_id"],
                description=parsed_commands.description[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
