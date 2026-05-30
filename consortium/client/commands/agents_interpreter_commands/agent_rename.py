from argparse import ArgumentParser

from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.agent_command_utils import rename_agent
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentRenameCommand(BaseCommand):
    name = "rename"
    description = "Set the name of an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to rename.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="New name for the agent.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await rename_agent(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id[0],
                name=parsed_args.name[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
