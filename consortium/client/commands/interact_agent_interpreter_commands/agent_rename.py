from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentRenameCommand as AgentRenameAgentsInterpreterCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentRenameCommand(AgentRenameAgentsInterpreterCommand):
    name = "rename"
    description = "Set the name of the current agent, or a specific agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          rename "New name"
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to rename (defaults to the current agent "
                "being interacted with if not provided)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "name",
            help="New name for the agent.",
            nargs=1,
        )

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_commands = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._rename_agent(
                rest_api=rest_api,
                agent_id=parsed_commands.agent_id
                if parsed_commands.agent_id
                else context.interpreter_context["agent"]["agent_id"],
                name=parsed_commands.name[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
