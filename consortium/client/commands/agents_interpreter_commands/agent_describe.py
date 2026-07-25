from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_command_utils import describe_agent
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentDescribeCommand(BaseConnectedCommand):
    name = "describe"
    description = "Set the description of an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          describe 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Agent Management Commands"
    autocompletes = Autocomplete.AGENT_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent whose description should be changed.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="New description for the agent.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await describe_agent(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id[0],
                description=parsed_args.description[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
