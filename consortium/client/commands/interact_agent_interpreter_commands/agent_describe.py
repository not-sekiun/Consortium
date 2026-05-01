from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    AgentDescribeCommand as AgentDescribeAgentsInterpreterCommand,
)
from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentDescribeCommand(AgentDescribeAgentsInterpreterCommand):
    name = "describe"
    description = (
        "Set the description of the current agent, or a specific agent by its ID"
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

    async def run(self, context: Context) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._describe_agent(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id
                else context.interpreter_context["agent"]["agent_id"],
                description=parsed_args.description[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
