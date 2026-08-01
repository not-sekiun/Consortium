from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchInteractAgentInterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class AgentInteractCommand(BaseConnectedCommand):
    name = "interact"
    description = "Interact with an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          interact 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    group = "Agent Management Commands"
    autocompletes = Autocomplete.AGENT_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to interact with.",
            nargs=1,
            default=None,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent = await rest_api.get_agent_by_agent_id(
                parsed_args.agent_id[0],
            )
            print_success(
                f"Interacting with agent: '{agent['name']}' ({agent['agent_id']})"
            )
            return SwitchInteractAgentInterpreterSignal(
                agent=agent,
            )
        except SystemExit:
            pass

        return ContinueSignal()
