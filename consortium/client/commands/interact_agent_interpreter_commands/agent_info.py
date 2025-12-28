from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentInfoCommand as InfoAgentAgentsInterpreterCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentInfoCommand(InfoAgentAgentsInterpreterCommand):
    name = "info"
    description = (
        "Display information about the current agent, or a specific agent by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info
          info 123e4567-e89b-12d3-a456-42661417400
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

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_agent_info(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id is not None
                else context.environment["agent"]["agent_id"],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
