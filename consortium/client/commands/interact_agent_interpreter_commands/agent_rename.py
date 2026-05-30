from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.agent_command_utils import rename_agent
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentRenameCommand(BaseCommand[ConnectedContext]):
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

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await rename_agent(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id
                else context.interpreter_context.agent["agent_id"],
                name=parsed_args.name[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
