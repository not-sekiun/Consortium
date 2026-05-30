from argparse import ArgumentParser

from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.agent_command_utils import display_agent_info
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentInfoCommand(BaseCommand):
    name = "info"
    description = (
        "Display information about the current agent, or a specific agent by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info -v
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
        parser.add_argument(
            "-v",
            "--verbose",
            help=(
                "Display verbose information about the agent, including detailed "
                "agent capability information."
            ),
            action="store_true",
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await display_agent_info(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id is not None
                else context.interpreter_context["agent"]["agent_id"],
                verbose=parsed_args.verbose,
            )
        except SystemExit:
            pass

        return ContinueSignal()
